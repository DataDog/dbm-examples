import os
from aws_cdk import (
    Duration,
    Environment,
    RemovalPolicy,
    aws_applicationautoscaling as autoscaling,
    aws_ec2 as ec2,
    aws_iam as iam,
    aws_rds as rds,
    SecretValue,
    Stack,
    # aws_sqs as sqs,
)
from constructs import Construct


class AuroraPostgresIamStack(Stack):
    def __init__(self, scope: Construct, construct_id: str, env: Environment, **kwargs) -> None:
        super().__init__(scope, construct_id, env=env)

        ############################### VPC ###############################
        vpc_id = kwargs.get("vpc_id")
        if not vpc_id:
            raise ValueError("vpc_id is required")
        vpc = ec2.Vpc.from_lookup(self, "vpc", vpc_id=vpc_id)

        subnets = ec2.SubnetSelection()
        ############################### VPC ###############################

        ############################### Security Group ###############################
        dd_agent_security_group = ec2.SecurityGroup(
            self,
            "dd-agent-security-group",
            vpc=vpc,
            allow_all_outbound=True,
        )

        aurora_cluster_security_group = ec2.SecurityGroup(
            self,
            "aurora-cluster-security-group",
            vpc=vpc,
            allow_all_outbound=True,
        )

        aurora_cluster_security_group.add_ingress_rule(
            peer=dd_agent_security_group,
            connection=ec2.Port.tcp(5432),
            description="allow dd-agent to connect to aurora cluster",
        )
        ############################### Security Group ###############################

        ############################### Aurora Cluster ###############################
        version = rds.AuroraPostgresEngineVersion.VER_15_5

        aurora_cluster = rds.DatabaseCluster(
            self,
            "aurora-cluster",
            engine=rds.DatabaseClusterEngine.aurora_postgres(version=version),
            writer=rds.ClusterInstance.provisioned(
                "writer",
                instance_type=ec2.InstanceType.of(
                    ec2.InstanceClass.BURSTABLE3, ec2.InstanceSize.MEDIUM
                ),
            ),
            readers=[
                rds.ClusterInstance.provisioned(
                    "reader1",
                    instance_type=ec2.InstanceType.of(
                        ec2.InstanceClass.BURSTABLE3, ec2.InstanceSize.MEDIUM
                    ),
                ),
            ],
            credentials=rds.Credentials.from_generated_secret("postgres"),
            vpc=vpc,
            security_groups=[aurora_cluster_security_group],
            vpc_subnets=subnets,
            # Refer to https://docs.datadoghq.com/database_monitoring/setup_postgres/aurora?tab=postgres10#configure-postgres-settings
            parameter_group=rds.ParameterGroup(
                self,
                "aurora-postgres-15-parameter-group",
                engine=rds.DatabaseClusterEngine.aurora_postgres(version=version),
                parameters={
                    "shared_preload_libraries": "pg_stat_statements",
                    "track_activity_query_size": "4096",
                    "pg_stat_statements.track": "ALL",
                    "pg_stat_statements.max": "10000",
                    "pg_stat_statements.track_utility": "off",
                    "track_io_timing": "on",
                },
            ),
            deletion_protection=False,
            removal_policy=RemovalPolicy.DESTROY,
            iam_authentication=True,
        )

        # define read replica scaling target
        scaling_target = autoscaling.ScalableTarget(
            self,
            "aurora-scaling-target",
            max_capacity=4,
            min_capacity=1,
            resource_id=f"cluster:{aurora_cluster.cluster_identifier}",
            service_namespace=autoscaling.ServiceNamespace.RDS,
            scalable_dimension="rds:cluster:ReadReplicaCount",
        )

        # scale read replicas on cpu and connections
        scaling_target.scale_to_track_metric(
            "aurora-scale-readers-on-cpu",
            predefined_metric=autoscaling.PredefinedMetric.RDS_READER_AVERAGE_CPU_UTILIZATION,
            target_value=50,
            scale_in_cooldown=Duration.seconds(60),
            scale_out_cooldown=Duration.seconds(60),
        )
        scaling_target.scale_to_track_metric(
            "aurora-scale-readers-on-connections",
            predefined_metric=autoscaling.PredefinedMetric.RDS_READER_AVERAGE_DATABASE_CONNECTIONS,
            target_value=50,
            scale_in_cooldown=Duration.seconds(60),
            scale_out_cooldown=Duration.seconds(60),
        )
        ############################### Aurora Cluster ###############################

        ############################### Datadog Agent ###############################
        ssh_key_pair = kwargs.get("ssh_key_pair")
        if not ssh_key_pair:
            raise ValueError("ssh_key_pair is required")

        dd_agent = ec2.Instance(
            self,
            "dd-agent",
            instance_type=ec2.InstanceType.of(
                ec2.InstanceClass.BURSTABLE3, ec2.InstanceSize.MEDIUM
            ),
            vpc=vpc,
            machine_image=ec2.MachineImage.latest_amazon_linux2023(),
            security_group=dd_agent_security_group,
            vpc_subnets=subnets,
            associate_public_ip_address=False,
            key_pair=ec2.KeyPair.from_key_pair_name(
                self, "dd-agent-ssh-key-pair", ssh_key_pair
            ),
            require_imdsv2=True,
        )

        # attach inline policy to dd-agent role
        dd_agent.role.attach_inline_policy(
            iam.Policy(
                self,
                "dd-agent-policy",
                statements=[
                    iam.PolicyStatement(
                        actions=[
                            "rds-db:connect",
                        ],
                        resources=[
                            f"arn:aws:rds-db:*:{self.account}:dbuser:{aurora_cluster.cluster_resource_identifier}/datadog",
                        ],
                        effect=iam.Effect.ALLOW,
                    )
                ],
            )
        )

        # install postgresql client
        dd_agent.user_data.add_commands(
            "sudo dnf update -y && sudo dnf install -y postgresql15"
        )

        # Grant permissions to dd-agent to connect to aurora cluster
        # https://docs.datadoghq.com/database_monitoring/setup_postgres/aurora?tab=postgres10#grant-the-agent-access
        aurora_cluster.secret.grant_read(dd_agent)

        dd_agent.user_data.add_commands(
            *[
                f"export PGHOST={aurora_cluster.cluster_endpoint.hostname}",
                f"export PGUSER=$(aws secretsmanager get-secret-value --secret-id {aurora_cluster.secret.secret_name} --region {self.region} --query SecretString --output text | jq -r .username)",
                f"export PGPASSWORD=$(aws secretsmanager get-secret-value --secret-id {aurora_cluster.secret.secret_name} --region {self.region} --query SecretString --output text | jq -r .password)",
                "export PGDATABASE=postgres",
                "psql <<'EOF'",
                "CREATE USER datadog WITH LOGIN;",
                "GRANT rds_iam TO datadog;",
                "ALTER ROLE datadog INHERIT;",
                "CREATE SCHEMA datadog;",
                "GRANT USAGE ON SCHEMA datadog TO datadog;",
                "GRANT USAGE ON SCHEMA public TO datadog;",
                "GRANT pg_monitor TO datadog;",
                "CREATE EXTENSION IF NOT EXISTS pg_stat_statements;",
                "CREATE OR REPLACE FUNCTION datadog.explain_statement(l_query TEXT, OUT explain JSON) RETURNS SETOF JSON AS $$DECLARE curs REFCURSOR; plan JSON; BEGIN OPEN curs FOR EXECUTE pg_catalog.concat('EXPLAIN (FORMAT JSON) ', l_query); FETCH curs INTO plan; CLOSE curs; RETURN QUERY SELECT plan; END;$$ LANGUAGE 'plpgsql' RETURNS NULL ON NULL INPUT SECURITY DEFINER;",
                "EOF",
            ]
        )

        # Install Datadog Agent
        dd_api_key = os.getenv("DD_API_KEY")
        if not dd_api_key:
            raise ValueError("dd_api_key is required")

        dd_agent.user_data.add_commands(
            f'DD_API_KEY={dd_api_key} DD_SITE="datadoghq.com" DD_APM_INSTRUMENTATION_ENABLED=host  bash -c "$(curl -L https://s3.amazonaws.com/dd-agent/scripts/install_script_agent7.sh)"'
        )

        # Update postgres integration config
        with open(os.path.join(os.path.dirname(__file__), "conf.yaml")) as f:
            config = f.read().format(
                writer_endpoint=aurora_cluster.cluster_endpoint.hostname,
                reader_endpoint=aurora_cluster.instance_endpoints[0].hostname,
            )
            dd_agent.user_data.add_commands(
                *[
                    "cat << EOF > /etc/datadog-agent/conf.d/postgres.d/conf.yaml",
                    config,
                    "EOF",
                    "sudo systemctl restart datadog-agent",
                ]
            )

        dd_agent.node.add_dependency(aurora_cluster)
        ############################### Datadog Agent ###############################

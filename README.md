# dbm-examples

The repository includes example applications and configurations for Datadog Database Monitoring.

## Examples

### AWS

#### Aurora PostgreSQL IAM

[aws/aurora-postgres-iam](aws/aurora-postgres-iam) is a Datadog Database Monitoring example that monitors an Aurora PostgreSQL Cluster with IAM authentication enabled. The datadog agent is deployed on an EC2 instance in the same VPC as the Aurora PostgreSQL Cluster. The agent is configured to monitor the Aurora PostgreSQL Cluster using the [Datadog Database Monitoring for Aurora managed Postgres](https://docs.datadoghq.com/database_monitoring/setup_postgres/aurora/?tab=postgres10).

#### Aurora PostgreSQL Auto Discover (Beta)

[aws/aurora-postgres-autodiscover](aws/aurora-postgres-autodiscover) is a Datadog Database Monitoring example that monitors an Aurora PostgreSQL Cluster with database host endpoints auto discovery enabled. The datadog agent is deployed on an EC2 instance in the same VPC as the Aurora PostgreSQL Cluster. The agent is configured to monitor the Aurora PostgreSQL Cluster using the [Datadog Database Monitoring for Aurora managed Postgres](https://docs.datadoghq.com/database_monitoring/setup_postgres/aurora/?tab=postgres10).

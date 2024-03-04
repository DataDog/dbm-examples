import aws_cdk as core
import aws_cdk.assertions as assertions

from aurora_postgres_autodiscover.aurora_postgres_autodiscover_stack import AuroraPostgresAutodiscoverStack

# example tests. To run these tests, uncomment this file along with the example
# resource in aurora_postgres_autodiscover/aurora_postgres_autodiscover_stack.py
def test_sqs_queue_created():
    app = core.App()
    stack = AuroraPostgresAutodiscoverStack(app, "aurora-postgres-autodiscover")
    template = assertions.Template.from_stack(stack)

#     template.has_resource_properties("AWS::SQS::Queue", {
#         "VisibilityTimeout": 300
#     })

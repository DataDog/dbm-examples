import aws_cdk as core
import aws_cdk.assertions as assertions

from aurora_postgres_iam.aurora_postgres_iam_stack import AuroraPostgresIamStack

# example tests. To run these tests, uncomment this file along with the example
# resource in aurora_postgres_iam/aurora_postgres_iam_stack.py
def test_sqs_queue_created():
    app = core.App()
    stack = AuroraPostgresIamStack(app, "aurora-postgres-iam")
    template = assertions.Template.from_stack(stack)

#     template.has_resource_properties("AWS::SQS::Queue", {
#         "VisibilityTimeout": 300
#     })

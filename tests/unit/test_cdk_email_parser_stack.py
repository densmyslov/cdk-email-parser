import aws_cdk as core
import aws_cdk.assertions as assertions

from cdk_email_parser.cdk_email_parser_stack import CdkEmailParserStack

# example tests. To run these tests, uncomment this file along with the example
# resource in cdk_email_parser/cdk_email_parser_stack.py
def test_sqs_queue_created():
    app = core.App()
    stack = CdkEmailParserStack(app, "cdk-email-parser")
    template = assertions.Template.from_stack(stack)

#     template.has_resource_properties("AWS::SQS::Queue", {
#         "VisibilityTimeout": 300
#     })

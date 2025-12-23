import aws_cdk as core
import aws_cdk.assertions as assertions

from aws_quantiica_fraud_detector_poc.aws_quantiica_fraud_detector_poc_stack import AwsQuantiicaFraudDetectorPocStack

# example tests. To run these tests, uncomment this file along with the example
# resource in aws_quantiica_fraud_detector_poc/aws_quantiica_fraud_detector_poc_stack.py
def test_sqs_queue_created():
    app = core.App()
    stack = AwsQuantiicaFraudDetectorPocStack(app, "aws-quantiica-fraud-detector-poc")
    template = assertions.Template.from_stack(stack)

#     template.has_resource_properties("AWS::SQS::Queue", {
#         "VisibilityTimeout": 300
#     })

from aws_cdk import (
    Stack,
    aws_lambda as _lambda,
    aws_lambda_event_sources as lambda_event_sources,
    aws_dynamodb as dynamodb,
    aws_sqs as sqs,
)
from constructs import Construct


class EventSourceMappingStack(Stack):
    def __init__(
        self,
        scope: Construct,
        construct_id: str,
        *,
        project_prefix: str,
        environment: str = "dev",
        stream_processor_lambda: _lambda.Function,
        fraud_detector_lambda: _lambda.DockerImageFunction,
        transaction_updater_lambda: _lambda.Function,
        transactions_table: dynamodb.TableV2,
        input_queue: sqs.Queue,
        output_queue: sqs.Queue,
        **kwargs,
    ) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # DynamoDB Stream → Stream Processor Lambda
        stream_processor_lambda.add_event_source(
            lambda_event_sources.DynamoEventSource(
                table=transactions_table,
                starting_position=_lambda.StartingPosition.LATEST,
                batch_size=10,
                retry_attempts=2,
            )
        )

        # SQS Input Queue → Fraud Detector Lambda
        fraud_detector_lambda.add_event_source(
            lambda_event_sources.SqsEventSource(
                queue=input_queue,
                batch_size=1,
            )
        )

        # SQS Output Queue → Transaction Updater Lambda
        transaction_updater_lambda.add_event_source(
            lambda_event_sources.SqsEventSource(
                queue=output_queue,
                batch_size=1,
            )
        )

from aws_cdk import Stack, Duration, aws_sqs as sqs
from constructs import Construct


class SQSStack(Stack):
    def __init__(
        self,
        scope: Construct,
        construct_id: str,
        *,
        project_prefix: str,
        environment: str = "dev",
        **kwargs,
    ) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # Input Queue: Receives new transactions from DynamoDB Stream
        transactions_input_queue = sqs.Queue(
            self,
            "TransactionsInputQueue",
            queue_name=f"{project_prefix}-transactions-input-{environment}.fifo".lower(),
            visibility_timeout=Duration.seconds(300),
            retention_period=Duration.days(14),
            content_based_deduplication=True,
            fifo=True,
        )

        # Output Queue: Receives analyzed results from Docker Lambda
        transactions_output_queue = sqs.Queue(
            self,
            "TransactionsOutputQueue",
            queue_name=f"{project_prefix}-transactions-output-{environment}.fifo".lower(),
            visibility_timeout=Duration.seconds(60),
            retention_period=Duration.days(14),
            content_based_deduplication=True,
            fifo=True,
        )

        self.transactions_input_queue = transactions_input_queue
        self.transactions_output_queue = transactions_output_queue

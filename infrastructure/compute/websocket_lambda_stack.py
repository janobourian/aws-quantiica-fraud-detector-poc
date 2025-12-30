from aws_cdk import (
    Stack,
    Duration,
    Size,
    aws_lambda as _lambda,
    aws_iam as iam,
)
from constructs import Construct


class WebSocketLambdaStack(Stack):
    def __init__(
        self,
        scope: Construct,
        construct_id: str,
        *,
        project_prefix: str,
        environment: str = "dev",
        connections_table_name: str,
        connections_table_arn: str,
        transactions_table_name: str,
        transactions_table_arn: str,
        transactions_stream_arn: str,
        clients_table_name: str,
        clients_table_arn: str,
        counterparties_table_name: str,
        counterparties_table_arn: str,
        clients_tx_state_table_name: str,
        clients_tx_state_table_arn: str,
        client_recent_activity_table_name: str,
        client_recent_activity_table_arn: str,
        websocket_api_id: str,
        websocket_endpoint: str,
        input_queue_url: str,
        input_queue_arn: str,
        output_queue_url: str,
        output_queue_arn: str,
        **kwargs,
    ) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # WebSocket Connect Lambda
        connect_lambda = _lambda.Function(
            self,
            "WebSocketConnectFunction",
            runtime=_lambda.Runtime.PYTHON_3_12,
            handler="index.handler",
            code=_lambda.Code.from_asset("assets/backend/lambdas/websocket_connect"),
            function_name=f"{project_prefix}-websocket-connect-{environment}".lower(),
            timeout=Duration.seconds(30),
            environment={
                "CONNECTIONS_TABLE_NAME": connections_table_name,
            },
        )

        # WebSocket Disconnect Lambda
        disconnect_lambda = _lambda.Function(
            self,
            "WebSocketDisconnectFunction",
            runtime=_lambda.Runtime.PYTHON_3_12,
            handler="index.handler",
            code=_lambda.Code.from_asset("assets/backend/lambdas/websocket_disconnect"),
            function_name=f"{project_prefix}-websocket-disconnect-{environment}".lower(),
            timeout=Duration.seconds(30),
            environment={
                "CONNECTIONS_TABLE_NAME": connections_table_name,
            },
        )

        # WebSocket Default Lambda
        default_lambda = _lambda.Function(
            self,
            "WebSocketDefaultFunction",
            runtime=_lambda.Runtime.PYTHON_3_12,
            handler="index.handler",
            code=_lambda.Code.from_asset("assets/backend/lambdas/websocket_default"),
            function_name=f"{project_prefix}-websocket-default-{environment}".lower(),
            timeout=Duration.seconds(30),
        )

        # DynamoDB Stream Processor Lambda
        stream_processor_lambda = _lambda.Function(
            self,
            "StreamProcessorFunction",
            runtime=_lambda.Runtime.PYTHON_3_12,
            handler="index.handler",
            code=_lambda.Code.from_asset("assets/backend/lambdas/stream_processor"),
            function_name=f"{project_prefix}-stream-processor-{environment}".lower(),
            timeout=Duration.seconds(60),
            environment={
                "SQS_QUEUE_URL": input_queue_url,
                "WEBSOCKET_ENDPOINT": websocket_endpoint,
                "CONNECTIONS_TABLE_NAME": connections_table_name,
            },
        )

        fraud_detector_lambda = _lambda.DockerImageFunction(
            self,
            "FraudDetectorFunction",
            code=_lambda.DockerImageCode.from_image_asset(
                "assets/backend/lambdas/fraud_detector_docker"
            ),
            function_name=f"{project_prefix}-fraud-detector-{environment}".lower(),
            timeout=Duration.seconds(900),
            architecture=_lambda.Architecture.ARM_64,
            memory_size=3008,
            ephemeral_storage_size=Size.mebibytes(2048),
            environment={
                "OUTPUT_QUEUE_URL": output_queue_url,
                "TRANSACTIONS_TABLE_NAME": transactions_table_name,
                "CLIENTS_TABLE_NAME": clients_table_name,
                "COUNTERPARTIES_TABLE_NAME": counterparties_table_name,
                "CLIENT_TX_STATE_TABLE_NAME": clients_tx_state_table_name,
                "CLIENT_RECENT_ACTIVITY_TABLE_NAME": client_recent_activity_table_name,
            },
        )

        # Transaction Updater Lambda
        transaction_updater_lambda = _lambda.Function(
            self,
            "TransactionUpdaterFunction",
            runtime=_lambda.Runtime.PYTHON_3_12,
            handler="index.handler",
            code=_lambda.Code.from_asset("assets/backend/lambdas/transaction_updater"),
            function_name=f"{project_prefix}-transaction-updater-{environment}".lower(),
            timeout=Duration.seconds(60),
            environment={
                "TRANSACTIONS_TABLE_NAME": transactions_table_name,
                "CONNECTIONS_TABLE_NAME": connections_table_name,
                "WEBSOCKET_ENDPOINT": websocket_endpoint,
            },
        )

        # Grant permissions
        connect_lambda.add_to_role_policy(
            iam.PolicyStatement(
                actions=["dynamodb:PutItem"],
                resources=[connections_table_arn],
            )
        )

        disconnect_lambda.add_to_role_policy(
            iam.PolicyStatement(
                actions=["dynamodb:DeleteItem"],
                resources=[connections_table_arn],
            )
        )

        stream_processor_lambda.add_to_role_policy(
            iam.PolicyStatement(
                actions=["sqs:SendMessage"],
                resources=[input_queue_arn],
            )
        )
        stream_processor_lambda.add_to_role_policy(
            iam.PolicyStatement(
                actions=["dynamodb:Scan", "dynamodb:DeleteItem"],
                resources=[connections_table_arn],
            )
        )
        stream_processor_lambda.add_to_role_policy(
            iam.PolicyStatement(
                actions=["execute-api:ManageConnections"],
                resources=[
                    f"arn:aws:execute-api:{self.region}:{self.account}:{websocket_api_id}/*"
                ],
            )
        )

        fraud_detector_lambda.add_to_role_policy(
            iam.PolicyStatement(
                actions=["sqs:SendMessage"],
                resources=[output_queue_arn],
            )
        )
        fraud_detector_lambda.add_to_role_policy(
            iam.PolicyStatement(
                actions=["dynamodb:Scan"],
                resources=[
                    clients_table_arn,
                    counterparties_table_arn,
                    clients_tx_state_table_arn,
                    client_recent_activity_table_arn,
                    transactions_table_arn,
                ],
            )
        )
        fraud_detector_lambda.add_to_role_policy(
            iam.PolicyStatement(
                actions=["dynamodb:UpdateItem"],
                resources=[transactions_table_arn],
            )
        )

        transaction_updater_lambda.add_to_role_policy(
            iam.PolicyStatement(
                actions=["dynamodb:UpdateItem", "dynamodb:GetItem"],
                resources=[transactions_table_arn],
            )
        )
        transaction_updater_lambda.add_to_role_policy(
            iam.PolicyStatement(
                actions=["dynamodb:Scan", "dynamodb:DeleteItem"],
                resources=[connections_table_arn],
            )
        )
        transaction_updater_lambda.add_to_role_policy(
            iam.PolicyStatement(
                actions=["execute-api:ManageConnections"],
                resources=[
                    f"arn:aws:execute-api:{self.region}:{self.account}:{websocket_api_id}/*"
                ],
            )
        )

        self.connect_lambda = connect_lambda
        self.disconnect_lambda = disconnect_lambda
        self.default_lambda = default_lambda
        self.stream_processor_lambda = stream_processor_lambda
        self.fraud_detector_lambda = fraud_detector_lambda
        self.transaction_updater_lambda = transaction_updater_lambda

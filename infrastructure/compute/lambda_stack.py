from aws_cdk import Stack, Duration, aws_lambda as _lambda, aws_iam as iam
from constructs import Construct


class LambdaStack(Stack):
    def __init__(
        self,
        scope: Construct,
        construct_id: str,
        *,
        project_prefix: str,
        environment: str = "dev",
        clients_table_name: str,
        clients_table_arn: str,
        transactions_table_name: str,
        transactions_table_arn: str,
        counterparties_table_name: str,
        counterparties_table_arn: str,
        clients_tx_state_table_name: str,
        clients_tx_state_table_arn: str,
        client_recent_activity_table_name: str,
        client_recent_activity_table_arn: str,
        **kwargs,
    ) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # POST Client Lambda
        post_client_lambda = _lambda.Function(
            self,
            "PostClientFunction",
            runtime=_lambda.Runtime.PYTHON_3_12,
            handler="index.handler",
            code=_lambda.Code.from_asset("assets/backend/lambdas/post_client"),
            function_name=f"{project_prefix}-post-client-{environment}".lower(),
            timeout=Duration.seconds(30),
            environment={
                "CLIENTS_TABLE_NAME": clients_table_name,
                "ENVIRONMENT": environment,
            },
        )

        # GET Clients Lambda
        get_clients_lambda = _lambda.Function(
            self,
            "GetClientsFunction",
            runtime=_lambda.Runtime.PYTHON_3_12,
            handler="index.handler",
            code=_lambda.Code.from_asset("assets/backend/lambdas/get_clients"),
            function_name=f"{project_prefix}-get-clients-{environment}".lower(),
            timeout=Duration.seconds(60),
            memory_size=1024,
            environment={
                "CLIENTS_TABLE_NAME": clients_table_name,
                "ENVIRONMENT": environment,
            },
        )

        # POST Transaction Lambda
        post_transaction_lambda = _lambda.Function(
            self,
            "PostTransactionFunction",
            runtime=_lambda.Runtime.PYTHON_3_12,
            handler="index.handler",
            code=_lambda.Code.from_asset("assets/backend/lambdas/post_transaction"),
            function_name=f"{project_prefix}-post-transaction-{environment}".lower(),
            timeout=Duration.seconds(30),
            environment={
                "TRANSACTIONS_TABLE_NAME": transactions_table_name,
                "ENVIRONMENT": environment,
            },
        )

        # GET Transactions Lambda
        get_transactions_lambda = _lambda.Function(
            self,
            "GetTransactionsFunction",
            runtime=_lambda.Runtime.PYTHON_3_12,
            handler="index.handler",
            code=_lambda.Code.from_asset("assets/backend/lambdas/get_transactions"),
            function_name=f"{project_prefix}-get-transactions-{environment}".lower(),
            timeout=Duration.seconds(60),
            memory_size=1024,
            environment={
                "TRANSACTIONS_TABLE_NAME": transactions_table_name,
                "ENVIRONMENT": environment,
            },
        )

        # Grant DynamoDB permissions
        post_client_lambda.add_to_role_policy(
            iam.PolicyStatement(
                actions=["dynamodb:PutItem"],
                resources=[clients_table_arn],
            )
        )

        get_clients_lambda.add_to_role_policy(
            iam.PolicyStatement(
                actions=["dynamodb:Scan", "dynamodb:Query"],
                resources=[clients_table_arn],
            )
        )

        post_transaction_lambda.add_to_role_policy(
            iam.PolicyStatement(
                actions=["dynamodb:PutItem"],
                resources=[transactions_table_arn],
            )
        )

        get_transactions_lambda.add_to_role_policy(
            iam.PolicyStatement(
                actions=["dynamodb:Scan", "dynamodb:Query"],
                resources=[transactions_table_arn],
            )
        )

        # POST Counterparty Lambda
        post_counterparty_lambda = _lambda.Function(
            self,
            "PostCounterpartyFunction",
            runtime=_lambda.Runtime.PYTHON_3_12,
            handler="index.handler",
            code=_lambda.Code.from_asset("assets/backend/lambdas/post_counterparty"),
            function_name=f"{project_prefix}-post-counterparty-{environment}".lower(),
            timeout=Duration.seconds(30),
            environment={
                "COUNTERPARTIES_TABLE_NAME": counterparties_table_name,
                "ENVIRONMENT": environment,
            },
        )

        # GET Counterparties Lambda
        get_counterparties_lambda = _lambda.Function(
            self,
            "GetCounterpartiesFunction",
            runtime=_lambda.Runtime.PYTHON_3_12,
            handler="index.handler",
            code=_lambda.Code.from_asset("assets/backend/lambdas/get_counterparties"),
            function_name=f"{project_prefix}-get-counterparties-{environment}".lower(),
            timeout=Duration.seconds(60),
            memory_size=1024,
            environment={
                "COUNTERPARTIES_TABLE_NAME": counterparties_table_name,
                "ENVIRONMENT": environment,
            },
        )

        post_counterparty_lambda.add_to_role_policy(
            iam.PolicyStatement(
                actions=["dynamodb:PutItem"],
                resources=[counterparties_table_arn],
            )
        )

        get_counterparties_lambda.add_to_role_policy(
            iam.PolicyStatement(
                actions=["dynamodb:Scan", "dynamodb:Query"],
                resources=[counterparties_table_arn],
            )
        )

        # POST Client Tx State Lambda
        post_client_tx_state_lambda = _lambda.Function(
            self,
            "PostClientTxStateFunction",
            runtime=_lambda.Runtime.PYTHON_3_12,
            handler="index.handler",
            code=_lambda.Code.from_asset("assets/backend/lambdas/post_client_tx_state"),
            function_name=f"{project_prefix}-post-client-tx-state-{environment}".lower(),
            timeout=Duration.seconds(30),
            environment={
                "TABLE_NAME": clients_tx_state_table_name,
                "ENVIRONMENT": environment,
            },
        )

        # GET Clients Tx State Lambda
        get_clients_tx_state_lambda = _lambda.Function(
            self,
            "GetClientsTxStateFunction",
            runtime=_lambda.Runtime.PYTHON_3_12,
            handler="index.handler",
            code=_lambda.Code.from_asset("assets/backend/lambdas/get_clients_tx_state"),
            function_name=f"{project_prefix}-get-clients-tx-state-{environment}".lower(),
            timeout=Duration.seconds(30),
            environment={
                "TABLE_NAME": clients_tx_state_table_name,
                "ENVIRONMENT": environment,
            },
        )

        post_client_tx_state_lambda.add_to_role_policy(
            iam.PolicyStatement(
                actions=["dynamodb:PutItem"],
                resources=[clients_tx_state_table_arn],
            )
        )

        get_clients_tx_state_lambda.add_to_role_policy(
            iam.PolicyStatement(
                actions=["dynamodb:Scan", "dynamodb:Query"],
                resources=[clients_tx_state_table_arn],
            )
        )

        # POST Client Recent Activity Lambda
        post_client_recent_activity_lambda = _lambda.Function(
            self,
            "PostClientRecentActivityFunction",
            runtime=_lambda.Runtime.PYTHON_3_12,
            handler="index.handler",
            code=_lambda.Code.from_asset(
                "assets/backend/lambdas/post_client_recent_activity"
            ),
            function_name=f"{project_prefix}-post-client-recent-activity-{environment}".lower(),
            timeout=Duration.seconds(30),
            environment={
                "TABLE_NAME": client_recent_activity_table_name,
                "ENVIRONMENT": environment,
            },
        )

        # GET Client Recent Activity Lambda
        get_client_recent_activity_lambda = _lambda.Function(
            self,
            "GetClientRecentActivityFunction",
            runtime=_lambda.Runtime.PYTHON_3_12,
            handler="index.handler",
            code=_lambda.Code.from_asset(
                "assets/backend/lambdas/get_client_recent_activity"
            ),
            function_name=f"{project_prefix}-get-client-recent-activity-{environment}".lower(),
            timeout=Duration.seconds(30),
            environment={
                "TABLE_NAME": client_recent_activity_table_name,
                "ENVIRONMENT": environment,
            },
        )

        post_client_recent_activity_lambda.add_to_role_policy(
            iam.PolicyStatement(
                actions=["dynamodb:PutItem"],
                resources=[client_recent_activity_table_arn],
            )
        )

        get_client_recent_activity_lambda.add_to_role_policy(
            iam.PolicyStatement(
                actions=["dynamodb:Scan", "dynamodb:Query"],
                resources=[client_recent_activity_table_arn],
            )
        )

        self.post_client_lambda = post_client_lambda
        self.get_clients_lambda = get_clients_lambda
        self.post_transaction_lambda = post_transaction_lambda
        self.get_transactions_lambda = get_transactions_lambda
        self.post_counterparty_lambda = post_counterparty_lambda
        self.get_counterparties_lambda = get_counterparties_lambda
        self.post_client_tx_state_lambda = post_client_tx_state_lambda
        self.get_clients_tx_state_lambda = get_clients_tx_state_lambda
        self.post_client_recent_activity_lambda = post_client_recent_activity_lambda
        self.get_client_recent_activity_lambda = get_client_recent_activity_lambda

from aws_cdk import (
    Stack,
    aws_apigatewayv2 as apigwv2,
    aws_lambda as _lambda,
    aws_iam as iam,
)
from constructs import Construct


class ApiIntegrationStack(Stack):
    def __init__(
        self,
        scope: Construct,
        construct_id: str,
        *,
        project_prefix: str,
        environment: str = "dev",
        http_api_id: str,
        post_client_lambda: _lambda.Function,
        get_clients_lambda: _lambda.Function,
        post_transaction_lambda: _lambda.Function,
        get_transactions_lambda: _lambda.Function,
        post_counterparty_lambda: _lambda.Function,
        get_counterparties_lambda: _lambda.Function,
        post_client_tx_state_lambda: _lambda.Function,
        get_clients_tx_state_lambda: _lambda.Function,
        post_client_recent_activity_lambda: _lambda.Function,
        get_client_recent_activity_lambda: _lambda.Function,
        **kwargs,
    ) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # POST /clients
        post_client_integration = apigwv2.CfnIntegration(
            self,
            "PostClientIntegration",
            api_id=http_api_id,
            integration_type="AWS_PROXY",
            integration_uri=post_client_lambda.function_arn,
            payload_format_version="2.0",
        )
        apigwv2.CfnRoute(
            self,
            "PostClientRoute",
            api_id=http_api_id,
            route_key="POST /clients",
            target=f"integrations/{post_client_integration.ref}",
        )
        post_client_lambda.add_permission(
            "ApiGatewayInvoke",
            principal=iam.ServicePrincipal("apigateway.amazonaws.com"),
            source_arn=f"arn:aws:execute-api:{self.region}:{self.account}:{http_api_id}/*/*",
        )

        # GET /clients
        get_clients_integration = apigwv2.CfnIntegration(
            self,
            "GetClientsIntegration",
            api_id=http_api_id,
            integration_type="AWS_PROXY",
            integration_uri=get_clients_lambda.function_arn,
            payload_format_version="2.0",
        )
        apigwv2.CfnRoute(
            self,
            "GetClientsRoute",
            api_id=http_api_id,
            route_key="GET /clients",
            target=f"integrations/{get_clients_integration.ref}",
        )
        get_clients_lambda.add_permission(
            "ApiGatewayInvoke",
            principal=iam.ServicePrincipal("apigateway.amazonaws.com"),
            source_arn=f"arn:aws:execute-api:{self.region}:{self.account}:{http_api_id}/*/*",
        )

        # POST /transactions
        post_transaction_integration = apigwv2.CfnIntegration(
            self,
            "PostTransactionIntegration",
            api_id=http_api_id,
            integration_type="AWS_PROXY",
            integration_uri=post_transaction_lambda.function_arn,
            payload_format_version="2.0",
        )
        apigwv2.CfnRoute(
            self,
            "PostTransactionRoute",
            api_id=http_api_id,
            route_key="POST /transactions",
            target=f"integrations/{post_transaction_integration.ref}",
        )
        post_transaction_lambda.add_permission(
            "ApiGatewayInvoke",
            principal=iam.ServicePrincipal("apigateway.amazonaws.com"),
            source_arn=f"arn:aws:execute-api:{self.region}:{self.account}:{http_api_id}/*/*",
        )

        # GET /transactions
        get_transactions_integration = apigwv2.CfnIntegration(
            self,
            "GetTransactionsIntegration",
            api_id=http_api_id,
            integration_type="AWS_PROXY",
            integration_uri=get_transactions_lambda.function_arn,
            payload_format_version="2.0",
        )
        apigwv2.CfnRoute(
            self,
            "GetTransactionsRoute",
            api_id=http_api_id,
            route_key="GET /transactions",
            target=f"integrations/{get_transactions_integration.ref}",
        )
        get_transactions_lambda.add_permission(
            "ApiGatewayInvoke",
            principal=iam.ServicePrincipal("apigateway.amazonaws.com"),
            source_arn=f"arn:aws:execute-api:{self.region}:{self.account}:{http_api_id}/*/*",
        )

        # POST /counterparties
        post_counterparty_integration = apigwv2.CfnIntegration(
            self,
            "PostCounterpartyIntegration",
            api_id=http_api_id,
            integration_type="AWS_PROXY",
            integration_uri=post_counterparty_lambda.function_arn,
            payload_format_version="2.0",
        )
        apigwv2.CfnRoute(
            self,
            "PostCounterpartyRoute",
            api_id=http_api_id,
            route_key="POST /counterparties",
            target=f"integrations/{post_counterparty_integration.ref}",
        )
        post_counterparty_lambda.add_permission(
            "ApiGatewayInvoke",
            principal=iam.ServicePrincipal("apigateway.amazonaws.com"),
            source_arn=f"arn:aws:execute-api:{self.region}:{self.account}:{http_api_id}/*/*",
        )

        # GET /counterparties
        get_counterparties_integration = apigwv2.CfnIntegration(
            self,
            "GetCounterpartiesIntegration",
            api_id=http_api_id,
            integration_type="AWS_PROXY",
            integration_uri=get_counterparties_lambda.function_arn,
            payload_format_version="2.0",
        )
        apigwv2.CfnRoute(
            self,
            "GetCounterpartiesRoute",
            api_id=http_api_id,
            route_key="GET /counterparties",
            target=f"integrations/{get_counterparties_integration.ref}",
        )
        get_counterparties_lambda.add_permission(
            "ApiGatewayInvoke",
            principal=iam.ServicePrincipal("apigateway.amazonaws.com"),
            source_arn=f"arn:aws:execute-api:{self.region}:{self.account}:{http_api_id}/*/*",
        )

        # POST /clients-tx-state
        post_client_tx_state_integration = apigwv2.CfnIntegration(
            self,
            "PostClientTxStateIntegration",
            api_id=http_api_id,
            integration_type="AWS_PROXY",
            integration_uri=post_client_tx_state_lambda.function_arn,
            payload_format_version="2.0",
        )
        apigwv2.CfnRoute(
            self,
            "PostClientTxStateRoute",
            api_id=http_api_id,
            route_key="POST /clients-tx-state",
            target=f"integrations/{post_client_tx_state_integration.ref}",
        )
        post_client_tx_state_lambda.add_permission(
            "ApiGatewayInvoke",
            principal=iam.ServicePrincipal("apigateway.amazonaws.com"),
            source_arn=f"arn:aws:execute-api:{self.region}:{self.account}:{http_api_id}/*/*",
        )

        # GET /clients-tx-state
        get_clients_tx_state_integration = apigwv2.CfnIntegration(
            self,
            "GetClientsTxStateIntegration",
            api_id=http_api_id,
            integration_type="AWS_PROXY",
            integration_uri=get_clients_tx_state_lambda.function_arn,
            payload_format_version="2.0",
        )
        apigwv2.CfnRoute(
            self,
            "GetClientsTxStateRoute",
            api_id=http_api_id,
            route_key="GET /clients-tx-state",
            target=f"integrations/{get_clients_tx_state_integration.ref}",
        )
        get_clients_tx_state_lambda.add_permission(
            "ApiGatewayInvoke",
            principal=iam.ServicePrincipal("apigateway.amazonaws.com"),
            source_arn=f"arn:aws:execute-api:{self.region}:{self.account}:{http_api_id}/*/*",
        )

        # POST /client-recent-activity
        post_client_recent_activity_integration = apigwv2.CfnIntegration(
            self,
            "PostClientRecentActivityIntegration",
            api_id=http_api_id,
            integration_type="AWS_PROXY",
            integration_uri=post_client_recent_activity_lambda.function_arn,
            payload_format_version="2.0",
        )
        apigwv2.CfnRoute(
            self,
            "PostClientRecentActivityRoute",
            api_id=http_api_id,
            route_key="POST /client-recent-activity",
            target=f"integrations/{post_client_recent_activity_integration.ref}",
        )
        post_client_recent_activity_lambda.add_permission(
            "ApiGatewayInvoke",
            principal=iam.ServicePrincipal("apigateway.amazonaws.com"),
            source_arn=f"arn:aws:execute-api:{self.region}:{self.account}:{http_api_id}/*/*",
        )

        # GET /client-recent-activity
        get_client_recent_activity_integration = apigwv2.CfnIntegration(
            self,
            "GetClientRecentActivityIntegration",
            api_id=http_api_id,
            integration_type="AWS_PROXY",
            integration_uri=get_client_recent_activity_lambda.function_arn,
            payload_format_version="2.0",
        )
        apigwv2.CfnRoute(
            self,
            "GetClientRecentActivityRoute",
            api_id=http_api_id,
            route_key="GET /client-recent-activity",
            target=f"integrations/{get_client_recent_activity_integration.ref}",
        )
        get_client_recent_activity_lambda.add_permission(
            "ApiGatewayInvoke",
            principal=iam.ServicePrincipal("apigateway.amazonaws.com"),
            source_arn=f"arn:aws:execute-api:{self.region}:{self.account}:{http_api_id}/*/*",
        )

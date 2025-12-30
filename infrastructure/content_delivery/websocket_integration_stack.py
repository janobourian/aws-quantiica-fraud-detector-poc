from aws_cdk import (
    Stack,
    aws_apigatewayv2 as apigwv2,
    aws_iam as iam,
    aws_lambda as _lambda,
)
from constructs import Construct


class WebSocketIntegrationStack(Stack):
    def __init__(
        self,
        scope: Construct,
        construct_id: str,
        *,
        project_prefix: str,
        environment: str = "dev",
        websocket_api_id: str,
        connect_lambda: _lambda.Function,
        disconnect_lambda: _lambda.Function,
        default_lambda: _lambda.Function,
        **kwargs,
    ) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # $connect route
        connect_integration = apigwv2.CfnIntegration(
            self,
            "ConnectIntegration",
            api_id=websocket_api_id,
            integration_type="AWS_PROXY",
            integration_uri=f"arn:aws:apigateway:{self.region}:lambda:path/2015-03-31/functions/{connect_lambda.function_arn}/invocations",
        )
        apigwv2.CfnRoute(
            self,
            "ConnectRoute",
            api_id=websocket_api_id,
            route_key="$connect",
            target=f"integrations/{connect_integration.ref}",
        )
        connect_lambda.add_permission(
            "WebSocketConnectInvoke",
            principal=iam.ServicePrincipal("apigateway.amazonaws.com"),
            source_arn=f"arn:aws:execute-api:{self.region}:{self.account}:{websocket_api_id}/*",
        )

        # $disconnect route
        disconnect_integration = apigwv2.CfnIntegration(
            self,
            "DisconnectIntegration",
            api_id=websocket_api_id,
            integration_type="AWS_PROXY",
            integration_uri=f"arn:aws:apigateway:{self.region}:lambda:path/2015-03-31/functions/{disconnect_lambda.function_arn}/invocations",
        )
        apigwv2.CfnRoute(
            self,
            "DisconnectRoute",
            api_id=websocket_api_id,
            route_key="$disconnect",
            target=f"integrations/{disconnect_integration.ref}",
        )
        disconnect_lambda.add_permission(
            "WebSocketDisconnectInvoke",
            principal=iam.ServicePrincipal("apigateway.amazonaws.com"),
            source_arn=f"arn:aws:execute-api:{self.region}:{self.account}:{websocket_api_id}/*",
        )

        # $default route
        default_integration = apigwv2.CfnIntegration(
            self,
            "DefaultIntegration",
            api_id=websocket_api_id,
            integration_type="AWS_PROXY",
            integration_uri=f"arn:aws:apigateway:{self.region}:lambda:path/2015-03-31/functions/{default_lambda.function_arn}/invocations",
        )
        apigwv2.CfnRoute(
            self,
            "DefaultRoute",
            api_id=websocket_api_id,
            route_key="$default",
            target=f"integrations/{default_integration.ref}",
        )
        default_lambda.add_permission(
            "WebSocketDefaultInvoke",
            principal=iam.ServicePrincipal("apigateway.amazonaws.com"),
            source_arn=f"arn:aws:execute-api:{self.region}:{self.account}:{websocket_api_id}/*",
        )

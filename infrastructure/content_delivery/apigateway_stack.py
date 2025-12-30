from aws_cdk import Stack, CfnOutput, aws_apigatewayv2 as apigwv2
from constructs import Construct


class ApiGatewayStack(Stack):
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

        # WebSocket API
        websocket_api = apigwv2.CfnApi(
            self,
            "WebSocketApi",
            name=f"{project_prefix}-websocket-api-{environment}".lower(),
            protocol_type="WEBSOCKET",
            route_selection_expression="$request.body.action",
        )

        apigwv2.CfnStage(
            self,
            "WebSocketStage",
            api_id=websocket_api.ref,
            stage_name=environment,
            auto_deploy=True,
            default_route_settings=apigwv2.CfnStage.RouteSettingsProperty(
                throttling_burst_limit=5000,
                throttling_rate_limit=10000,
            ),
        )

        # HTTP API for REST endpoints
        http_api = apigwv2.CfnApi(
            self,
            "HttpApi",
            name=f"{project_prefix}-http-api-{environment}".lower(),
            protocol_type="HTTP",
            cors_configuration=apigwv2.CfnApi.CorsProperty(
                allow_origins=["*"],
                allow_methods=["GET", "POST", "OPTIONS"],
                allow_headers=["*"],
            ),
        )

        apigwv2.CfnStage(
            self,
            "HttpStage",
            api_id=http_api.ref,
            stage_name=environment,
            auto_deploy=True,
        )

        # Outputs
        CfnOutput(
            self,
            "WebSocketApiId",
            value=websocket_api.ref,
            export_name=f"{project_prefix}-WebSocketApiId-{environment}",
        )
        CfnOutput(
            self,
            "WebSocketApiUrl",
            value=f"wss://{websocket_api.ref}.execute-api.{self.region}.amazonaws.com/{environment}",
            export_name=f"{project_prefix}-WebSocketApiUrl-{environment}",
        )
        CfnOutput(
            self,
            "HttpApiId",
            value=http_api.ref,
            export_name=f"{project_prefix}-HttpApiId-{environment}",
        )
        CfnOutput(
            self,
            "HttpApiUrl",
            value=f"https://{http_api.ref}.execute-api.{self.region}.amazonaws.com/{environment}",
            export_name=f"{project_prefix}-HttpApiUrl-{environment}",
        )

        self.websocket_api = websocket_api
        self.http_api = http_api
        self.http_api_id = http_api.ref
        self.http_stage_name = environment

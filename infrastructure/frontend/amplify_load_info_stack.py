from aws_cdk import Stack, CfnOutput, aws_amplify as amplify, aws_iam as iam
from constructs import Construct


class AmplifyLoadInfoStack(Stack):
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

        service_role = iam.Role(
            self,
            "AmplifyServiceRole",
            assumed_by=iam.ServicePrincipal("amplify.amazonaws.com"),
            managed_policies=[
                iam.ManagedPolicy.from_aws_managed_policy_name(
                    "AdministratorAccess-Amplify"
                )
            ],
        )

        app = amplify.CfnApp(
            self,
            "LoadInfoApp",
            name=f"{project_prefix}-load-info-{environment}".lower(),
            description="Quantiica Load Info Frontend",
            platform="WEB",
            iam_service_role=service_role.role_arn,
        )

        branch = amplify.CfnBranch(
            self,
            "MainBranch",
            app_id=app.attr_app_id,
            branch_name="main",
            enable_auto_build=False,
        )

        CfnOutput(
            self,
            "AmplifyAppUrl",
            value=f"https://main.{app.attr_default_domain}",
        )

        self.app = app
        self.branch = branch

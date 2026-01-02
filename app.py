#!/usr/bin/env python3
import os
import aws_cdk as cdk
from dotenv import load_dotenv
from infrastructure.databases.dynamodb_stack import DynamoDBStack
from infrastructure.content_delivery.apigateway_stack import ApiGatewayStack
from infrastructure.content_delivery.api_integration_stack import ApiIntegrationStack
from infrastructure.content_delivery.websocket_integration_stack import (
    WebSocketIntegrationStack,
)
from infrastructure.compute.lambda_stack import LambdaStack
from infrastructure.compute.websocket_lambda_stack import WebSocketLambdaStack
from infrastructure.app_integration.sqs_stack import SQSStack
from infrastructure.app_integration.event_source_mapping_stack import (
    EventSourceMappingStack,
)
from infrastructure.frontend.amplify_load_info_stack import AmplifyLoadInfoStack
from infrastructure.frontend.amplify_dashboard_stack import AmplifyDashboardStack

load_dotenv()

app = cdk.App()

project_prefix = os.getenv("PROJECT_PREFIX", "frauddetectorpoc")
environment_name = os.getenv("ENVIRONMENT", "dev")
account = os.getenv("ACCOUNT")
region = os.getenv("REGION", "us-east-1")
environment = cdk.Environment(account=account, region=region)
tags = {
    "Project": project_prefix,
    "Environment": environment_name,
    "CostCenter": os.getenv("COST_CENTER", "664010"),
    "Owner": os.getenv("OWNER", "frauddetectorpoc"),
}

storage_dynamodb_stack = DynamoDBStack(
    app,
    f"{project_prefix}-dynamodb-stack-{environment_name}",
    project_prefix=project_prefix,
    environment=environment_name,
    env=environment,
    tags=tags,
    description="DynamoDB Stack for Fraud Detector POC",
)

lambda_stack = LambdaStack(
    app,
    f"{project_prefix}-lambda-stack-{environment_name}",
    project_prefix=project_prefix,
    environment=environment_name,
    clients_table_name=storage_dynamodb_stack.clients_table.table_name,
    clients_table_arn=storage_dynamodb_stack.clients_table.table_arn,
    transactions_table_name=storage_dynamodb_stack.transactions_table.table_name,
    transactions_table_arn=storage_dynamodb_stack.transactions_table.table_arn,
    counterparties_table_name=storage_dynamodb_stack.counterparties_table.table_name,
    counterparties_table_arn=storage_dynamodb_stack.counterparties_table.table_arn,
    clients_tx_state_table_name=storage_dynamodb_stack.clients_tx_state_table.table_name,
    clients_tx_state_table_arn=storage_dynamodb_stack.clients_tx_state_table.table_arn,
    client_recent_activity_table_name=storage_dynamodb_stack.client_recent_activity_table.table_name,
    client_recent_activity_table_arn=storage_dynamodb_stack.client_recent_activity_table.table_arn,
    env=environment,
    tags=tags,
    description="Lambda Stack for Fraud Detector POC",
)

apigateway_stack = ApiGatewayStack(
    app,
    f"{project_prefix}-apigateway-stack-{environment_name}",
    project_prefix=project_prefix,
    environment=environment_name,
    env=environment,
    tags=tags,
    description="API Gateway Stack for Fraud Detector POC",
)

sqs_stack = SQSStack(
    app,
    f"{project_prefix}-sqs-stack-{environment_name}",
    project_prefix=project_prefix,
    environment=environment_name,
    env=environment,
    tags=tags,
    description="SQS Stack for Fraud Detector POC",
)

websocket_lambda_stack = WebSocketLambdaStack(
    app,
    f"{project_prefix}-websocket-lambda-stack-{environment_name}",
    project_prefix=project_prefix,
    environment=environment_name,
    connections_table_name=storage_dynamodb_stack.connections_table.table_name,
    connections_table_arn=storage_dynamodb_stack.connections_table.table_arn,
    transactions_table_name=storage_dynamodb_stack.transactions_table.table_name,
    transactions_table_arn=storage_dynamodb_stack.transactions_table.table_arn,
    transactions_stream_arn=storage_dynamodb_stack.transactions_table.table_stream_arn,
    clients_table_name=storage_dynamodb_stack.clients_table.table_name,
    clients_table_arn=storage_dynamodb_stack.clients_table.table_arn,
    counterparties_table_name=storage_dynamodb_stack.counterparties_table.table_name,
    counterparties_table_arn=storage_dynamodb_stack.counterparties_table.table_arn,
    clients_tx_state_table_name=storage_dynamodb_stack.clients_tx_state_table.table_name,
    clients_tx_state_table_arn=storage_dynamodb_stack.clients_tx_state_table.table_arn,
    client_recent_activity_table_name=storage_dynamodb_stack.client_recent_activity_table.table_name,
    client_recent_activity_table_arn=storage_dynamodb_stack.client_recent_activity_table.table_arn,
    websocket_api_id=apigateway_stack.websocket_api.ref,
    websocket_endpoint=f"https://{apigateway_stack.websocket_api.ref}.execute-api.{region}.amazonaws.com/{environment_name}",
    input_queue_url=sqs_stack.transactions_input_queue.queue_url,
    input_queue_arn=sqs_stack.transactions_input_queue.queue_arn,
    output_queue_url=sqs_stack.transactions_output_queue.queue_url,
    output_queue_arn=sqs_stack.transactions_output_queue.queue_arn,
    env=environment,
    tags=tags,
    description="WebSocket Lambda Stack for Fraud Detector POC",
)

event_source_mapping_stack = EventSourceMappingStack(
    app,
    f"{project_prefix}-event-source-mapping-stack-{environment_name}",
    project_prefix=project_prefix,
    environment=environment_name,
    stream_processor_lambda=websocket_lambda_stack.stream_processor_lambda,
    fraud_detector_lambda=websocket_lambda_stack.fraud_detector_lambda,
    transaction_updater_lambda=websocket_lambda_stack.transaction_updater_lambda,
    transactions_table=storage_dynamodb_stack.transactions_table,
    input_queue=sqs_stack.transactions_input_queue,
    output_queue=sqs_stack.transactions_output_queue,
    env=environment,
    tags=tags,
    description="Event Source Mapping Stack for Fraud Detector POC",
)

websocket_integration_stack = WebSocketIntegrationStack(
    app,
    f"{project_prefix}-websocket-integration-stack-{environment_name}",
    project_prefix=project_prefix,
    environment=environment_name,
    websocket_api_id=apigateway_stack.websocket_api.ref,
    connect_lambda=websocket_lambda_stack.connect_lambda,
    disconnect_lambda=websocket_lambda_stack.disconnect_lambda,
    default_lambda=websocket_lambda_stack.default_lambda,
    env=environment,
    tags=tags,
    description="WebSocket Integration Stack for Fraud Detector POC",
)

api_integration_stack = ApiIntegrationStack(
    app,
    f"{project_prefix}-api-integration-stack-{environment_name}",
    project_prefix=project_prefix,
    environment=environment_name,
    http_api_id=apigateway_stack.http_api_id,
    post_client_lambda=lambda_stack.post_client_lambda,
    get_clients_lambda=lambda_stack.get_clients_lambda,
    post_transaction_lambda=lambda_stack.post_transaction_lambda,
    post_transaction_batch_lambda=lambda_stack.post_transaction_batch_lambda,
    get_transactions_lambda=lambda_stack.get_transactions_lambda,
    post_counterparty_lambda=lambda_stack.post_counterparty_lambda,
    get_counterparties_lambda=lambda_stack.get_counterparties_lambda,
    post_client_tx_state_lambda=lambda_stack.post_client_tx_state_lambda,
    get_clients_tx_state_lambda=lambda_stack.get_clients_tx_state_lambda,
    post_client_recent_activity_lambda=lambda_stack.post_client_recent_activity_lambda,
    get_client_recent_activity_lambda=lambda_stack.get_client_recent_activity_lambda,
    env=environment,
    tags=tags,
    description="API Integration Stack for Fraud Detector POC",
)

amplify_load_info_stack = AmplifyLoadInfoStack(
    app,
    f"{project_prefix}-amplify-load-info-stack-{environment_name}",
    project_prefix=project_prefix,
    environment=environment_name,
    env=environment,
    tags=tags,
    description="Amplify Load Info Frontend Stack for Fraud Detector POC",
)

amplify_dashboard_stack = AmplifyDashboardStack(
    app,
    f"{project_prefix}-amplify-dashboard-stack-{environment_name}",
    project_prefix=project_prefix,
    environment=environment_name,
    env=environment,
    tags=tags,
    description="Amplify Dashboard Frontend Stack for Fraud Detector POC",
)

lambda_stack.add_dependency(storage_dynamodb_stack)
api_integration_stack.add_dependency(apigateway_stack)
api_integration_stack.add_dependency(lambda_stack)
websocket_lambda_stack.add_dependency(storage_dynamodb_stack)
websocket_lambda_stack.add_dependency(sqs_stack)
websocket_lambda_stack.add_dependency(apigateway_stack)
event_source_mapping_stack.add_dependency(websocket_lambda_stack)
event_source_mapping_stack.add_dependency(storage_dynamodb_stack)
event_source_mapping_stack.add_dependency(sqs_stack)
websocket_integration_stack.add_dependency(websocket_lambda_stack)
websocket_integration_stack.add_dependency(apigateway_stack)
amplify_load_info_stack.add_dependency(api_integration_stack)
amplify_dashboard_stack.add_dependency(api_integration_stack)
amplify_dashboard_stack.add_dependency(websocket_integration_stack)

app.synth()

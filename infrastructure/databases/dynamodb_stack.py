from aws_cdk import Stack, aws_dynamodb as dynamodb
from constructs import Construct


class DynamoDBStack(Stack):
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

        clients_table = dynamodb.TableV2(
            self,
            "ClientsTable",
            partition_key=dynamodb.Attribute(
                name="client_id",
                type=dynamodb.AttributeType.STRING,
            ),
            table_name=f"{project_prefix}-clients-{environment}".lower(),
            deletion_protection=False,
            dynamo_stream=dynamodb.StreamViewType.NEW_AND_OLD_IMAGES,
        )

        transactions_table = dynamodb.TableV2(
            self,
            "TransactionsTable",
            partition_key=dynamodb.Attribute(
                name="transaction_id",
                type=dynamodb.AttributeType.STRING,
            ),
            table_name=f"{project_prefix}-transactions-{environment}".lower(),
            deletion_protection=False,
            dynamo_stream=dynamodb.StreamViewType.NEW_AND_OLD_IMAGES,
        )

        counterparties_table = dynamodb.TableV2(
            self,
            "CounterpartiesTable",
            partition_key=dynamodb.Attribute(
                name="counterparty_id",
                type=dynamodb.AttributeType.STRING,
            ),
            table_name=f"{project_prefix}-counterparties-{environment}".lower(),
            deletion_protection=False,
            dynamo_stream=dynamodb.StreamViewType.NEW_AND_OLD_IMAGES,
        )

        clients_tx_state_table = dynamodb.TableV2(
            self,
            "ClientsTxStateTable",
            partition_key=dynamodb.Attribute(
                name="client_tx_state_id",
                type=dynamodb.AttributeType.STRING,
            ),
            table_name=f"{project_prefix}-clients-tx-state-{environment}".lower(),
            deletion_protection=False,
            dynamo_stream=dynamodb.StreamViewType.NEW_AND_OLD_IMAGES,
        )

        client_recent_activity_table = dynamodb.TableV2(
            self,
            "ClientRecentActivityTable",
            partition_key=dynamodb.Attribute(
                name="client_recent_activity_id",
                type=dynamodb.AttributeType.STRING,
            ),
            table_name=f"{project_prefix}-client-recent-activity-{environment}".lower(),
            deletion_protection=False,
            dynamo_stream=dynamodb.StreamViewType.NEW_AND_OLD_IMAGES,
        )

        # WebSocket connections table
        connections_table = dynamodb.TableV2(
            self,
            "ConnectionsTable",
            partition_key=dynamodb.Attribute(
                name="connectionId",
                type=dynamodb.AttributeType.STRING,
            ),
            table_name=f"{project_prefix}-connections-{environment}".lower(),
            deletion_protection=False,
        )

        self.clients_table = clients_table
        self.transactions_table = transactions_table
        self.counterparties_table = counterparties_table
        self.clients_tx_state_table = clients_tx_state_table
        self.client_recent_activity_table = client_recent_activity_table
        self.connections_table = connections_table

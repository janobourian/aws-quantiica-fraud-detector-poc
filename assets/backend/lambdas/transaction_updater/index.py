import json
import os
import boto3
from datetime import datetime, timezone, timedelta
from decimal import Decimal

dynamodb = boto3.resource("dynamodb")
transactions_table = dynamodb.Table(os.environ["TRANSACTIONS_TABLE_NAME"])
connections_table = dynamodb.Table(os.environ["CONNECTIONS_TABLE_NAME"])

apigateway = boto3.client(
    "apigatewaymanagementapi", endpoint_url=os.environ["WEBSOCKET_ENDPOINT"]
)


def handler(event, context):
    print(f"Event: {event}")
    print(f"Context: {context}")
    try:
        for record in event["Records"]:
            result = json.loads(record["body"])

            mexico_tz = timezone(timedelta(hours=-6))
            now = datetime.now(mexico_tz).strftime("%Y-%m-%d %H:%M:%S")

            # Get transaction details to include client_account_id
            tx_response = transactions_table.get_item(
                Key={"transaction_id": result["transaction_id"]}
            )
            transaction = tx_response.get("Item", {})

            # Update transaction in DynamoDB
            transactions_table.update_item(
                Key={"transaction_id": result["transaction_id"]},
                UpdateExpression="SET #status = :status, risk_score = :score, risk_prediction = :prediction, explanation = :explanation, updated_at = :updated_at, last_status_at = :last_status_at",
                ExpressionAttributeNames={"#status": "status"},
                ExpressionAttributeValues={
                    ":status": "ANALYZED",
                    ":score": Decimal(str(result["risk_score"])),
                    ":prediction": result["risk_prediction"],
                    ":explanation": result["explanation"],
                    ":updated_at": now,
                    ":last_status_at": now,
                },
            )

            # Broadcast to WebSocket clients only if risk_score >= 0.5
            if result["risk_score"] >= 0.5:
                broadcast_message = {
                    "type": "analyzed_transaction",
                    "status": "ANALYZED",
                    "transaction_id": result["transaction_id"],
                    "risk_score": result["risk_score"],
                    "risk_prediction": result["risk_prediction"],
                    "client_account_id": transaction.get("client_account_id", ""),
                    "amount": float(transaction.get("amount", 0)),
                }
                broadcast_to_clients(broadcast_message)

            else:
                print(
                    f"Transaction {result['transaction_id']} has risk_score < 0.5, not broadcasting"
                )

        return {"statusCode": 200}
    except Exception as e:
        print(f"ERROR: {e}")
        print(f"Event: {event}")
        import traceback

        traceback.print_exc()
        return {"statusCode": 500}


def broadcast_to_clients(message):
    try:
        response = connections_table.scan()
        connections = response.get("Items", [])

        for connection in connections:
            try:
                apigateway.post_to_connection(
                    ConnectionId=connection["connectionId"],
                    Data=json.dumps(message).encode("utf-8"),
                )
            except Exception:
                connections_table.delete_item(
                    Key={"connectionId": connection["connectionId"]}
                )
    except Exception as e:
        print(f"Broadcast error: {e}")

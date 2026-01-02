import json
import os
import boto3

sqs = boto3.client("sqs")
apigateway = boto3.client(
    "apigatewaymanagementapi", endpoint_url=os.environ["WEBSOCKET_ENDPOINT"]
)
dynamodb = boto3.resource("dynamodb")
connections_table = dynamodb.Table(os.environ["CONNECTIONS_TABLE_NAME"])

queue_url = os.environ["SQS_QUEUE_URL"]


def handler(event, context):
    print(f"Event: {event}")
    print(f"Context: {context}")
    try:
        for record in event["Records"]:
            if record["eventName"] == "INSERT":
                new_image = record["dynamodb"]["NewImage"]

                # Debug: Print the amount field
                print(f"Amount field from DynamoDB: {new_image.get('amount', {})}")

                transaction_data = {
                    "transaction_id": new_image["transaction_id"]["S"],
                    "movement_type": new_image.get("movement_type", {}).get("S", ""),
                    "tx_type": new_image.get("tx_type", {}).get("S", ""),
                    "client_account_id": new_image.get("client_account_id", {}).get(
                        "S", ""
                    ),
                    "counterparty_account_id": new_image.get(
                        "counterparty_account_id", {}
                    ).get("S", ""),
                    "amount": float(new_image.get("amount", {}).get("N", "0")),
                    "created_at": new_image.get("created_at", {}).get("S", ""),
                    "risk_score": float(new_image.get("risk_score", {}).get("N", "0")),
                    "risk_prediction": new_image.get("risk_prediction", {}).get(
                        "S", ""
                    ),
                }

                # Debug: Print parsed amount
                print(f"Parsed amount: {transaction_data['amount']}")
                transaction_data["status"] = (
                    "ANALYZED" if transaction_data["risk_prediction"] else "STARTED"
                )

                # Send to SQS
                if transaction_data["status"] == "STARTED":
                    sqs.send_message(
                        QueueUrl=queue_url,
                        MessageBody=json.dumps(transaction_data),
                        MessageGroupId=transaction_data["transaction_id"],
                        MessageDeduplicationId=transaction_data["transaction_id"],
                    )

                    # Broadcast to WebSocket clients
                    broadcast_message = {
                        "type": "new_transaction",
                        "status": "STARTED",
                        "transaction_id": transaction_data["transaction_id"],
                        "amount": transaction_data["amount"],
                        "client_account_id": transaction_data["client_account_id"],
                        "counterparty_account_id": transaction_data[
                            "counterparty_account_id"
                        ],
                        "created_at": transaction_data["created_at"],
                        "movement_type": transaction_data["movement_type"],
                        "tx_type": transaction_data["tx_type"],
                    }

                    # Debug: Print broadcast message
                    print(f"Broadcasting message: {json.dumps(broadcast_message)}")
                    broadcast_to_clients(broadcast_message)

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

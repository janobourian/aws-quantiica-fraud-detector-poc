import json
import os
import boto3
from datetime import datetime, timezone, timedelta
from uuid import uuid4

dynamodb = boto3.resource("dynamodb")
table_name = os.environ["TRANSACTIONS_TABLE_NAME"]
table = dynamodb.Table(table_name)


def handler(event, context):
    print(f"Event: {event}")
    print(f"Context: {context}")
    try:
        body = json.loads(event.get("body", "{}"))

        mexico_tz = timezone(timedelta(hours=-6))
        now = datetime.now(mexico_tz).strftime("%Y-%m-%d %H:%M:%S")

        transaction_data = {
            "transaction_id": body.get("transaction_id") or str(uuid4()),
            "movement_type": body.get("movement_type"),
            "tx_type": body.get("tx_type"),
            "client_account_id": body.get("client_account_id"),
            "counterparty_account_id": body.get("counterparty_account_id"),
            "amount": body.get("amount"),
            "created_at": body.get("created_at") or now,
            "updated_at": now,
            "risk_score": body.get("risk_score"),
            "explanation": body.get("explanation"),
            "status": body.get("status", "STARTED"),
            "last_status_at": body.get("last_status_at") or now,
            "risk_prediction": body.get("risk_prediction", False),
        }

        table.put_item(Item=transaction_data)

        return {
            "statusCode": 200,
            "headers": {
                "Content-Type": "application/json",
                "Access-Control-Allow-Origin": "*",
            },
            "body": json.dumps(
                {
                    "message": "Transaction created",
                    "transaction_id": transaction_data["transaction_id"],
                }
            ),
        }
    except Exception as e:
        print(f"ERROR: {str(e)}")
        print(f"Event: {event}")
        import traceback

        traceback.print_exc()
        return {
            "statusCode": 500,
            "headers": {
                "Content-Type": "application/json",
                "Access-Control-Allow-Origin": "*",
            },
            "body": json.dumps({"error": str(e)}),
        }

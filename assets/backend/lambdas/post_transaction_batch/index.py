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

        with table.batch_writer() as batch:
            for transaction in body.get("transactions", []):
                transaction_data = {
                    "transaction_id": transaction.get("transaction_id") or str(uuid4()),
                    "movement_type": transaction.get("movement_type"),
                    "tx_type": transaction.get("tx_type"),
                    "client_account_id": transaction.get("client_account_id"),
                    "counterparty_account_id": transaction.get("counterparty_account_id"),
                    "amount": transaction.get("amount"),
                    "created_at": transaction.get("created_at") or now,
                    "updated_at": now,
                    "risk_score": transaction.get("risk_score"),
                    "explanation": transaction.get("explanation"),
                    "status": transaction.get("status", "STARTED"),
                    "last_status_at": transaction.get("last_status_at") or now,
                    "risk_prediction": transaction.get("risk_prediction", False),
                }

                if transaction_data["risk_score"] is not None:
                    transaction_data["risk_score"] = int(float(transaction_data["risk_score"])*100)

                batch.put_item(Item=transaction_data)

        return {
            "statusCode": 200,
            "headers": {
                "Content-Type": "application/json",
                "Access-Control-Allow-Origin": "*",
            },
            "body": json.dumps(
                {
                    "message": "Transaction created",
                    "transactions_length": len(body.get("transactions", [])),
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

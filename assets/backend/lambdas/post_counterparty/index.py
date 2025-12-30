import json
import os
import boto3
from datetime import datetime, timezone, timedelta
from uuid import uuid4

dynamodb = boto3.resource("dynamodb")
table_name = os.environ["COUNTERPARTIES_TABLE_NAME"]
table = dynamodb.Table(table_name)


def handler(event, context):
    print(f"Event: {event}")
    print(f"Context: {context}")
    try:
        body = json.loads(event.get("body", "{}"))

        mexico_tz = timezone(timedelta(hours=-6))
        now = datetime.now(mexico_tz).strftime("%Y-%m-%d %H:%M:%S")

        counterparty_data = {
            "counterparty_id": body.get("counterparty_id") or str(uuid4()),
            "person_type": body.get("person_type"),
            "account_id": body.get("account_id"),
            "country": body.get("country"),
            "city": body.get("city"),
            "state": body.get("state"),
            "industry": body.get("industry"),
            "risk_level": body.get("risk_level"),
            "is_client": body.get("is_client", False),
            "name": body.get("name"),
            "created_at": body.get("created_at") or now,
            "updated_at": now,
        }

        table.put_item(Item=counterparty_data)

        return {
            "statusCode": 200,
            "headers": {
                "Content-Type": "application/json",
                "Access-Control-Allow-Origin": "*",
            },
            "body": json.dumps(
                {
                    "message": "Counterparty created",
                    "counterparty_id": counterparty_data["counterparty_id"],
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

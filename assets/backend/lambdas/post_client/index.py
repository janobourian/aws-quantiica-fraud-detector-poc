import json
import os
import boto3
from datetime import datetime, timezone, timedelta
from uuid import uuid4

dynamodb = boto3.resource("dynamodb")
table_name = os.environ["CLIENTS_TABLE_NAME"]
table = dynamodb.Table(table_name)


def handler(event, context):
    print(f"Event: {event}")
    print(f"Context: {context}")
    try:
        body = json.loads(event.get("body", "{}"))

        mexico_tz = timezone(timedelta(hours=-6))
        now = datetime.now(mexico_tz).strftime("%Y-%m-%d %H:%M:%S")

        client_data = {
            "client_id": body.get("client_id") or str(uuid4()),
            "rfc": body.get("rfc"),
            "ocupation": body.get("ocupation"),
            "risk_level": body.get("risk_level"),
            "person_type": body.get("person_type"),
            "first_name": body.get("first_name"),
            "last_name": body.get("last_name"),
            "city": body.get("city"),
            "state": body.get("state"),
            "country": body.get("country"),
            "account_id": body.get("account_id"),
            "created_at": body.get("created_at") or now,
            "updated_at": now,
            "mean_amount_tx": body.get("mean_amount_tx", 0.0),
            "std_amount_tx": body.get("std_amount_tx", 0.0),
            "mean_volume_per_day_tx": body.get("mean_volume_per_day_tx", 0.0),
            "std_volume_per_day_tx": body.get("std_volume_per_day_tx", 0.0),
        }

        table.put_item(Item=client_data)

        return {
            "statusCode": 200,
            "headers": {
                "Content-Type": "application/json",
                "Access-Control-Allow-Origin": "*",
            },
            "body": json.dumps(
                {"message": "Client created", "client_id": client_data["client_id"]}
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

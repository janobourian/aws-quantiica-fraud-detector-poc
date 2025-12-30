import json
import os
import boto3
import uuid
from datetime import datetime, timezone, timedelta
from decimal import Decimal

dynamodb = boto3.resource("dynamodb")
table_name = os.environ["TABLE_NAME"]
table = dynamodb.Table(table_name)


def decimal_default(obj):
    if isinstance(obj, Decimal):
        return float(obj)
    raise TypeError


def handler(event, context):
    try:
        body = json.loads(event["body"])

        mexico_tz = timezone(timedelta(hours=-6))
        now = datetime.now(mexico_tz).strftime("%Y-%m-%d %H:%M:%S")

        item = {
            "client_tx_state_id": body.get("client_tx_state_id", str(uuid.uuid4())),
            "client_account_id": body["client_account_id"],
            "last_tx_timestamp": body.get("last_tx_timestamp", now),
            "tx_count": int(body.get("tx_count", 0)),
            "tx_sum": Decimal(str(body.get("tx_sum", 0.0))),
            "tx_square_sum": Decimal(str(body.get("tx_square_sum", 0.0))),
            "avg_tx_amount": Decimal(str(body.get("avg_tx_amount", 0.0))),
            "std_tx_amount": Decimal(str(body.get("std_tx_amount", 0.0))),
            "created_at": now,
            "updated_at": now,
        }

        table.put_item(Item=item)

        return {
            "statusCode": 200,
            "headers": {
                "Content-Type": "application/json",
                "Access-Control-Allow-Origin": "*",
            },
            "body": json.dumps(
                {"message": "Client tx state created"}, default=decimal_default
            ),
        }
    except Exception as e:
        print(f"ERROR: {str(e)}")
        print(f"Event body: {event.get('body', 'No body')}")
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

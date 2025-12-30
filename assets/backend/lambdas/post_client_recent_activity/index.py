import json
import os
import boto3
import uuid
from datetime import datetime, timezone, timedelta

dynamodb = boto3.resource("dynamodb")
table_name = os.environ["TABLE_NAME"]
table = dynamodb.Table(table_name)


def handler(event, context):
    try:
        body = json.loads(event["body"])

        mexico_tz = timezone(timedelta(hours=-6))
        now = datetime.now(mexico_tz).strftime("%Y-%m-%d %H:%M:%S")

        item = {
            "client_recent_activity_id": body.get(
                "client_recent_activity_id", str(uuid.uuid4())
            ),
            "client_account_id": body["client_account_id"],
            "bucket_timestamp": body.get("bucket_timestamp", now),
            "tx_count": int(body.get("tx_count", 0)),
            "unique_counterparties_count": int(
                body.get("unique_counterparties_count", 0)
            ),
            "unique_counterparties": body.get("unique_counterparties", ""),
            "created_at": body.get("created_at", now),
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
                {"message": "Client recent activity created", "item": item}
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

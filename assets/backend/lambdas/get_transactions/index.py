import json
import os
import boto3
from boto3.dynamodb.conditions import Attr
from decimal import Decimal

dynamodb = boto3.resource("dynamodb")
table_name = os.environ["TRANSACTIONS_TABLE_NAME"]
table = dynamodb.Table(table_name)


def decimal_default(obj):
    if isinstance(obj, Decimal):
        return int(obj) if obj % 1 == 0 else float(obj)
    raise TypeError


def handler(event, context):
    print(f"Event: {event}")
    print(f"Context: {context}")
    try:
        query_params = event.get("queryStringParameters") or {}
        account_id = query_params.get("account_id")

        if account_id:
            response = table.scan(
                FilterExpression=Attr("client_account_id").eq(account_id)
            )
        else:
            response = table.scan()

        items = response.get("Items", [])

        return {
            "statusCode": 200,
            "headers": {
                "Content-Type": "application/json",
                "Access-Control-Allow-Origin": "*",
            },
            "body": json.dumps({"transactions": items}, default=decimal_default),
        }
    except Exception as e:
        print(f"ERROR: {str(e)}")
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

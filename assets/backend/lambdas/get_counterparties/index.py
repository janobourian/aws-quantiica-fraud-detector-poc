import json
import os
import boto3

dynamodb = boto3.resource("dynamodb")
table_name = os.environ["COUNTERPARTIES_TABLE_NAME"]
table = dynamodb.Table(table_name)


def handler(event, context):
    print(f"Event: {event}")
    print(f"Context: {context}")
    try:
        response = table.scan(Limit=1000)
        items = response.get("Items", [])

        while "LastEvaluatedKey" in response:
            response = table.scan(
                Limit=1000, ExclusiveStartKey=response["LastEvaluatedKey"]
            )
            items.extend(response.get("Items", []))

        return {
            "statusCode": 200,
            "headers": {
                "Content-Type": "application/json",
                "Access-Control-Allow-Origin": "*",
            },
            "body": json.dumps({"counterparties": items}),
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

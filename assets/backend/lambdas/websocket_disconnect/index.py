import os
import boto3

dynamodb = boto3.resource("dynamodb")
table_name = os.environ["CONNECTIONS_TABLE_NAME"]
table = dynamodb.Table(table_name)


def handler(event, context):
    print(f"Event: {event}")
    print(f"Context: {context}")
    connection_id = event["requestContext"]["connectionId"]

    try:
        table.delete_item(Key={"connectionId": connection_id})
        return {"statusCode": 200, "body": "Disconnected"}
    except Exception as e:
        print(f"ERROR: {e}")
        print(f"Event: {event}")
        import traceback

        traceback.print_exc()
        return {"statusCode": 500, "body": "Failed to disconnect"}

def handler(event, context):
    print(f"Event: {event}")
    print(f"Context: {context}")
    return {"statusCode": 200, "body": "Default route"}

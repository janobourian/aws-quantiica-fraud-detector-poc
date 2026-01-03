import json
import os
import boto3
from decimal import Decimal
from main import load_all_tables, get_dynamic_features, init_predictor


sqs = boto3.client("sqs")
dynamodb = boto3.resource("dynamodb")
output_queue_url = os.environ["OUTPUT_QUEUE_URL"]
transactions_table = dynamodb.Table(os.environ["TRANSACTIONS_TABLE_NAME"])

# Global state for container reuse
data_loaded = False
predictor = None
transaction_data = None
clients_df = None
counterparties_df = None
client_tx_state_df = None
client_recent_activity_df = None


def handler(event, context):
    global data_loaded, predictor, transaction_data, clients_df, counterparties_df, client_tx_state_df, client_recent_activity_df

    print(f"Event: {event}")
    print(f"Body: {json.loads(event.get('Records', {})[0].get('body', {}))}")
    print(f"Context: {context}")

    try:
        print(f"Data loaded status: {data_loaded}")
        print(f"Predictor status: {predictor}")
        print(f"Init predictor status: {init_predictor}")

        if not data_loaded:
            print("Cargando datos por primera vez...")
            (
                transaction_data,
                clients_df,
                counterparties_df,
                client_tx_state_df,
                client_recent_activity_df,
            ) = load_all_tables()
            predictor = init_predictor()
            data_loaded = True
            print("Datos cargados y almacenados en memoria global")
        else:
            print("Usando datos previamente cargados (container reuse)")

        print(f"Transactions: {transaction_data}")
        print(f"Clients DF: {clients_df}")
        print(f"Counterparties DF: {counterparties_df}")
        print(f"Client TX State DF: {client_tx_state_df}")
        print(f"Client Recent Activity DF: {client_recent_activity_df}")

        for record in event["Records"]:
            print("Record: ", record)
            transaction_data = json.loads(record["body"])
            print("Predictor: ", predictor)
            print("Data loaded: ", data_loaded)

            try:
                if not transaction_data.get("timestamp"):
                    transaction_data["timestamp"] = transaction_data.get(
                        "created_at", ""
                    )

                calculated_features = get_dynamic_features(
                    transaction_data,
                    client_tx_state_df,
                    client_recent_activity_df,
                    clients_df,
                    counterparties_df,
                )

                print("Calculated features: ", calculated_features)

                transaction_data.update(calculated_features)
                print("Transaction data with features: ", transaction_data)

                transaction_data["transaction_id"] = transaction_data.get(
                    "transaction_id", "unknown"
                )
                results = predictor.predict_risk([transaction_data])
                print("Prediction results: ", results)

                result = {
                    "transaction_id": transaction_data["transaction_id"],
                    "risk_score": Decimal(str(results[0]["risk_probability"])),
                    "risk_prediction": results[0]["risk_prediction"],
                    "explanation": json.dumps(results[0].get("shap_explanation", {})),
                    "model_version": results[0].get("model_version", "unknown"),
                    "status": "ANALYZED",
                }

                # Update DynamoDB transaction before sending to SQS
                transactions_table.update_item(
                    Key={"transaction_id": result["transaction_id"]},
                    UpdateExpression="SET risk_score = :rs, risk_prediction = :rp, explanation = :ex, #st = :status",
                    ExpressionAttributeNames={"#st": "status"},
                    ExpressionAttributeValues={
                        ":rs": result["risk_score"],
                        ":rp": result["risk_prediction"],
                        ":ex": result["explanation"],
                        ":status": result["status"],
                    },
                )

                sqs.send_message(
                    QueueUrl=output_queue_url,
                    MessageBody=json.dumps(
                        {
                            **result,
                            "risk_score": float(
                                result["risk_score"]
                            ),  # Convert Decimal back to float for JSON
                        }
                    ),
                    MessageGroupId=result["transaction_id"],
                    MessageDeduplicationId=f"{result['transaction_id']}-result",
                )
            except Exception as e:
                print(f"Error en predicción: {e}")
        return {"statusCode": 200}
    except Exception as e:
        print(f"ERROR: {e}")
        print(f"Event: {event}")
        import traceback

        traceback.print_exc()
        return {"statusCode": 500}

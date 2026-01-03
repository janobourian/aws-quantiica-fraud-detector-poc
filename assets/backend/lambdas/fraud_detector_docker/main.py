from typing import Optional, Dict, Any
from datetime import datetime, timedelta
from dotenv import load_dotenv
import os
import polars as pl
import boto3
import logging
from inference import TransactionRiskPredictor

load_dotenv()

predictor = None
transactions_df = None
clients_df = None
counterparties_df = None
client_tx_state_df = None
client_recent_activity_df = None


def build_geo_risk_map():
    geo_risk = {
        # LOW_RISK_REGIONS
        "Canada": 0.1,
        "Germany": 0.1,
        "Japan": 0.1,
        # NEUTRAL_RISK_REGIONS
        "Mexico": 0.4,
        "Brazil": 0.4,
        "Spain": 0.4,
        "US": 0.4,
        # HIGH_RISK_REGIONS
        "Venezuela": 0.8,
        "Nigeria": 0.8,
        "Russia": 0.8,
        "Ukraine": 0.8,
        "China": 0.8,
    }
    return geo_risk


def configure_logging(level_name: str = None) -> logging.Logger:
    if not level_name:
        level_name = logging.INFO

    logging.basicConfig(
        level=level_name,
    )

    root = logging.getLogger()
    root.setLevel(level_name)

    return root


root = configure_logging()

logger = logging.getLogger(root.name)


def log_message(
    message: str, level: str = "info", logger: Optional[logging.Logger] = None
) -> None:
    if not logger:
        print(message)
    else:
        log_func = getattr(logger, level.lower(), logger.info)
        log_func(message)


def convert_risk_level_to_float(risk_int: int) -> float:
    """Convert integer risk level (1-5) to float (0.0-1.0)"""
    if risk_int <= 2:
        return 0.1  # LOW: 0-0.2
    elif risk_int == 3:
        return 0.35  # MEDIUM: 0.2-0.5
    elif risk_int == 4:
        return 0.6  # HIGH: 0.5-0.7
    else:
        return 0.8  # VERY_HIGH: >0.7


def init_predictor():
    """Initialize predictor safely with error handling"""
    try:
        if TransactionRiskPredictor is None:
            print("TransactionRiskPredictor not available")
            return None
        predictor = TransactionRiskPredictor()
        predictor.load_model()
        print("Predictor initialized successfully")
        return predictor
    except Exception as e:
        print(f"Error initializing predictor: {e}")
        return None


def load_dynamodb_table(
    table_name: str, decimal_to_float: list = None, decimal_to_int: list = None
) -> list:
    """Load DynamoDB table with pagination support for large datasets"""
    dynamodb = boto3.resource("dynamodb")
    table = dynamodb.Table(table_name)
    items = []
    count = 0

    response = table.scan(Limit=1000)
    items.extend(response["Items"])
    count += len(response["Items"])
    print(f"Cargados {count:,} items de {table_name}...")

    while "LastEvaluatedKey" in response:
        response = table.scan(
            ExclusiveStartKey=response["LastEvaluatedKey"], Limit=1000
        )
        items.extend(response["Items"])
        count += len(response["Items"])
        if count % 10000 == 0:
            print(f"Cargados {count:,} items de {table_name}...")

    for item in items:
        if decimal_to_float:
            for field in decimal_to_float:
                if field in item:
                    item[field] = float(item[field])
        if decimal_to_int:
            for field in decimal_to_int:
                if field in item:
                    item[field] = int(item[field])

    print(f"Total cargado de {table_name}: {len(items):,} items")
    return items


def load_transactions_data():
    """Load transactions from DynamoDB table"""
    try:
        items = load_dynamodb_table(
            os.environ.get("TRANSACTIONS_TABLE_NAME"),
            decimal_to_float=["amount", "risk_score"],
        )
        transactions_df = pl.DataFrame(items).with_columns(
            [
                pl.col("created_at")
                .str.strptime(pl.Datetime, "%Y-%m-%d %H:%M:%S")
                .alias("timestamp")
            ]
        )
        return transactions_df
    except Exception as e:
        print(f"Error cargando transacciones: {e}")
        return None


def load_clients_data():
    """Load clients from DynamoDB table"""
    try:
        items = load_dynamodb_table(
            os.environ.get("CLIENTS_TABLE_NAME"), decimal_to_int=["risk_level"]
        )
        clients_df = pl.DataFrame(items).with_columns(
            [pl.col("created_at").str.strptime(pl.Datetime, "%Y-%m-%d %H:%M:%S")]
        )
        return clients_df
    except Exception as e:
        print(f"Error cargando clientes: {e}")
        return None


def load_counterparties_data():
    """Load counterparties from DynamoDB table"""
    try:
        items = load_dynamodb_table(
            os.environ.get("COUNTERPARTIES_TABLE_NAME"), decimal_to_int=["risk_level"]
        )
        counterparties_df = pl.DataFrame(items)
        return counterparties_df
    except Exception as e:
        print(f"Error cargando contrapartes: {e}")
        return None


def load_client_tx_state_data():
    """Load client transaction state from DynamoDB table"""
    try:
        items = load_dynamodb_table(
            os.environ.get("CLIENT_TX_STATE_TABLE_NAME"),
            decimal_to_float=[
                "tx_sum",
                "tx_square_sum",
                "avg_tx_amount",
                "std_tx_amount",
            ],
            decimal_to_int=["tx_count"],
        )
        client_tx_state_df = pl.DataFrame(items).with_columns(
            [pl.col("last_tx_timestamp").str.strptime(pl.Datetime, "%Y-%m-%d %H:%M:%S")]
        )
        return client_tx_state_df
    except Exception as e:
        print(f"Error cargando client_tx_state: {e}")
        return None


def load_client_recent_activity_data():
    """Load client recent activity from DynamoDB table"""
    try:
        items = load_dynamodb_table(
            os.environ.get("CLIENT_RECENT_ACTIVITY_TABLE_NAME"),
            decimal_to_int=["tx_count", "unique_counterparties_count"],
        )
        client_recent_activity_df = pl.DataFrame(items).with_columns(
            [
                pl.col("bucket_timestamp").str.strptime(
                    pl.Datetime, "%Y-%m-%dT%H:%M:%S.%f"
                )
            ]
        )
        return client_recent_activity_df
    except Exception as e:
        print(f"Error cargando client_recent_activity: {e}")
        return None


def load_all_tables():
    """Load all DynamoDB tables"""
    print("Cargando todas las tablas...")
    transactions_df = load_transactions_data()
    clients_df = load_clients_data()
    counterparties_df = load_counterparties_data()
    client_tx_state_df = load_client_tx_state_data()
    client_recent_activity_df = load_client_recent_activity_data()
    print("Todas las tablas cargadas exitosamente")
    return (
        transactions_df,
        clients_df,
        counterparties_df,
        client_tx_state_df,
        client_recent_activity_df,
    )


def get_dynamic_features(
    transaction: Dict[str, Any],
    client_tx_state_df: pl.DataFrame,
    client_recent_activity_df: pl.DataFrame,
    clients_df: pl.DataFrame,
    counterparties_df: pl.DataFrame,
    calculate_mean_std: bool = True,
    logger: Optional[logging.Logger] = None,
) -> Dict[str, Any]:
    """Prepare Client and Transactions Info for a Inference Job over a transaction record."""

    DEFAULT_FEATURES = {
        "client_risk_level": 0.1,
        "client_geo_risk": 0.4,
        "counterparty_geo_risk": 0.4,
        "tx_count_1h": 1,
        "unique_cp_1d": 1,
        "mean_amount": transaction.get("amount", 0),
        "std_amount": 0.0,
        "day_part": "morning",
    }

    print(f"Calculando features dinámicas para la transacción: {transaction}")
    print("DataFrames recibidos:")
    print(f"client_tx_state_df: {client_tx_state_df}")
    print(f"client_recent_activity_df: {client_recent_activity_df}")
    print(f"clients_df: {clients_df}")
    print(f"counterparties_df: {counterparties_df}")

    if (
        client_tx_state_df is None
        or client_recent_activity_df is None
        or clients_df is None
        or counterparties_df is None
    ):
        log_message(
            "No hay datos históricos disponibles, usando valores por defecto",
            level="warning",
            logger=logger,
        )
        return DEFAULT_FEATURES

    try:
        client_account_id = transaction["client_account_id"]

        # Parse timestamp using strptime for "2025-06-15 17:22:27" format
        current_time = datetime.strptime(transaction["timestamp"], "%Y-%m-%d %H:%M:%S")
        hour = current_time.hour

        # if 6 <= hour < 12:
        #     day_part = "morning"
        # elif 12 <= hour < 18:
        #     day_part = "afternoon"
        # elif 18 <= hour < 24:
        #     day_part = "evening"
        # else:
        #     day_part = "night"
        day_part = "night"

        geo_risk_map = build_geo_risk_map()

        # Get client info with null check
        client_info = (
            clients_df.filter(pl.col("account_id") == client_account_id)
            if clients_df is not None and clients_df.shape[0] > 0
            else None
        )
        client_risk = (
            client_info.select(pl.col("risk_level")).item()
            if client_info is not None and client_info.shape[0] > 0
            else None
        )
        print("Client risk level: ", client_risk)
        client_country = (
            client_info.select(pl.col("country")).item()
            if client_info is not None and client_info.shape[0] > 0
            else "Mexico"
        )

        # Get counterparty info with null check
        counterparty_info = (
            counterparties_df.filter(
                pl.col("account_id") == transaction["counterparty_account_id"]
            )
            if counterparties_df is not None and counterparties_df.shape[0] > 0
            else None
        )

        counterparty_country = (
            counterparty_info.select(pl.col("country")).item()
            if counterparty_info is not None and counterparty_info.shape[0] > 0
            else "Mexico"
        )

        # 1. Calcular geo risks
        client_geo_risk = geo_risk_map.get(client_country, 0.4)
        counterparty_geo_risk = geo_risk_map.get(counterparty_country, 0.4)

        # Get client state with null check
        client_state = (
            client_tx_state_df.filter(
                (pl.col("client_account_id") == client_account_id)
            )
            if client_tx_state_df is not None and client_tx_state_df.shape[0] > 0
            else None
        )

        # 2. Calcular información de montos
        mean_amount = (
            client_state.select(pl.col("avg_tx_amount")).item()
            if client_state is not None and client_state.shape[0] > 0
            else transaction.get("amount", 0)
        )
        std_amount = (
            client_state.select(pl.col("std_tx_amount")).item()
            if client_state is not None and client_state.shape[0] > 0
            else 0.0
        )

        # 3. Calcular actividad reciente
        one_hour_ago = current_time - timedelta(hours=1)
        client_activity = (
            client_recent_activity_df.filter(
                (pl.col("client_account_id") == client_account_id)
                & (pl.col("bucket_timestamp") >= one_hour_ago)
                & (pl.col("bucket_timestamp") < current_time)
            )
            if client_recent_activity_df is not None
            and client_recent_activity_df.shape[0] > 0
            else None
        )

        tx_count_1h = (
            client_activity.select(pl.col("tx_count")).sum().item()
            if client_activity is not None and client_activity.shape[0] > 0
            else 0
        )

        one_day_ago = current_time - timedelta(days=1)
        client_activity_24h = (
            client_recent_activity_df.filter(
                (pl.col("client_account_id") == client_account_id)
                & (pl.col("bucket_timestamp") >= one_day_ago)
                & (pl.col("bucket_timestamp") < current_time)
            )
            if client_recent_activity_df is not None
            and client_recent_activity_df.shape[0] > 0
            else None
        )

        if client_activity_24h is not None and client_activity_24h.shape[0] > 0:
            # Usar Polars para procesar strings y obtener únicos
            unique_cp_1d = client_activity_24h.select(
                pl.col("unique_counterparties")
                .str.split(",")  # Dividir strings por coma
                .list.explode()  # Explotar listas a filas individuales
                .str.strip_chars()  # Limpiar espacios
                .filter(pl.col("unique_counterparties") != "")  # Filtrar vacíos
            ).n_unique(
                "unique_counterparties"
            )  # Contar únicos
        else:
            unique_cp_1d = 0

        calculated_features = {
            "client_risk_level": (
                convert_risk_level_to_float(client_risk) if client_risk else 0.1
            ),
            "client_geo_risk": client_geo_risk,
            "counterparty_geo_risk": counterparty_geo_risk,
            "tx_count_1h": tx_count_1h,
            "unique_cp_1d": unique_cp_1d,
            "mean_amount": mean_amount,
            "std_amount": std_amount,
            "day_part": day_part,
        }

        log_message(
            f"Features calculadas para cliente {client_account_id}: {calculated_features}",
            logger=logger,
        )
        return calculated_features

    except Exception as e:
        log_message(
            f"Error calculando features dinámicas: {e}", level="error", logger=logger
        )
        # Valores por defecto en caso de error
        return DEFAULT_FEATURES

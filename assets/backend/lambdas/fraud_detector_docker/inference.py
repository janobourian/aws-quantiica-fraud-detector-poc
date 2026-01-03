import joblib
import pandas as pd
import numpy as np
from datetime import datetime
import shap
import os
from typing import Dict, Any, List
import warnings

warnings.filterwarnings("ignore")


class TransactionRiskPredictor:
    def __init__(self, model_dir: str = None):
        self.model = None
        self.feature_transformer = None
        self.label_encoder = None
        self.explainer = None
        self.feature_names = None
        self.latest_timestamp = None
        self.model_dir = model_dir or self._find_latest_model()

    def _find_latest_model(self) -> str:
        """Encuentra el modelo más reciente en la carpeta raíz del lambda"""
        script_dir = os.path.dirname(os.path.abspath(__file__))

        model_files = [
            f
            for f in os.listdir(script_dir)
            if f.startswith("xgboost_model_") and f.endswith(".pkl")
        ]

        if not model_files:
            raise FileNotFoundError(f"No se encontraron modelos en: {script_dir}")

        model_files.sort(reverse=True)
        latest_model = model_files[0]
        print("lastest_model:", latest_model)

        timestamp = latest_model.split("xgboost_model_balanced_")[-1].replace(
            ".pkl", ""
        )
        self.latest_timestamp = timestamp

        return os.path.join(script_dir, latest_model)

    def load_model(self):
        """Cargar modelo y transformadores"""
        try:
            script_dir = os.path.dirname(os.path.abspath(__file__))

            model_path = f"xgboost_model_balanced_{self.latest_timestamp}.pkl"
            model_full_path = os.path.join(script_dir, model_path)
            self.model = joblib.load(model_full_path)

            transformer_path = (
                f"feature_transformer_balanced_{self.latest_timestamp}.pkl"
            )
            transformer_full_path = os.path.join(script_dir, transformer_path)
            self.feature_transformer = joblib.load(transformer_full_path)

            encoder_path = f"label_encoder_balanced_{self.latest_timestamp}.pkl"
            encoder_full_path = os.path.join(script_dir, encoder_path)
            self.label_encoder = joblib.load(encoder_full_path)

            self.feature_names = [
                "movement_type",
                "tx_type",
                "amount",
                "client_risk_level",
                "mean_amount",
                "std_amount",
                "client_geo_risk",
                "counterparty_geo_risk",
                "tx_count_1h",
                "unique_cp_1d",
                "day_part",
            ]

            print(f"[INFO] Modelo cargado exitosamente desde: {self.model_dir}")

        except Exception as e:
            raise Exception(f"Error cargando modelo: {str(e)}")

    def _prepare_transaction_features(
        self, transactions: List[Dict[str, Any]]
    ) -> pd.DataFrame:
        """Preparar features de una transacción individual"""

        features_list = []
        print("Preparing features for transactions:", transactions)
        for transaction in transactions:
            features_dict = {
                "movement_type": transaction.get("movement_type", "TRANSFER"),
                "tx_type": transaction.get("tx_type", "ONLINE"),
                "amount": float(transaction.get("amount", 0)),
                "client_risk_level": float(transaction.get("client_risk_level", 0.1)),
                "mean_amount": float(
                    transaction.get("mean_amount", transaction.get("amount", 0))
                ),
                "std_amount": float(transaction.get("std_amount", 0)),
                "client_geo_risk": float(transaction.get("client_geo_risk", 0)),
                "counterparty_geo_risk": float(
                    transaction.get("counterparty_geo_risk", 0)
                ),
                "tx_count_1h": int(transaction.get("tx_count_1h", 1)),
                "unique_cp_1d": int(transaction.get("unique_cp_1d", 1)),
                "day_part": transaction.get("day_part", "morning"),
            }
            features_list.append(features_dict)

        return pd.DataFrame(features_list)

    def predict_risk(self, transactions: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Predecir riesgo de una transacción y generar explicación SHAP"""

        if self.model is None:
            self.load_model()

        processed_tx = []

        # Preparar features
        features_df = self._prepare_transaction_features(transactions)
        print("Features DataFrame:", features_df)

        # Transformar features
        X_transformed = self.feature_transformer.transform(features_df)

        # Predicción
        risk_probability = [
            float(value) for value in self.model.predict_proba(X_transformed)[:, 1]
        ]
        risk_prediction = [int(value) for value in self.model.predict(X_transformed)]
        print("Risk probabilities:", risk_probability)
        print("Risk predictions:", risk_prediction)

        # Generar explicación SHAP
        shap_explanations = self._generate_shap_explanation(X_transformed, features_df)
        print("SHAP explanations:", shap_explanations)

        print("Preparing final results...")
        for idx, transaction in enumerate(transactions):
            risk_level = self._interpret_risk_level(risk_probability[idx])

            processed_tx.append(
                {
                    "transaction_id": transaction.get("transaction_id", "unknown"),
                    "risk_probability": round(risk_probability[idx], 4),
                    "risk_prediction": bool(risk_prediction[idx]),
                    "risk_level": risk_level,
                    "shap_explanation": shap_explanations[idx],
                    "model_version": os.path.basename(self.model_dir),
                    "prediction_timestamp": datetime.now().isoformat(),
                }
            )

        return processed_tx

    def _generate_shap_explanation(
        self, X_transformed: np.ndarray, original_features: pd.DataFrame
    ) -> List[Dict[str, Any]]:
        """Generar explicación SHAP para múltiples transacciones"""

        try:
            if self.explainer is None:
                self.explainer = shap.TreeExplainer(self.model)

            shap_values = self.explainer.shap_values(X_transformed)
            print("shap_values shape:", np.array(shap_values).shape)

            # Obtener nombres de features transformadas
            feature_names_transformed = None
            if hasattr(self.feature_transformer, "get_feature_names_out"):
                feature_names_transformed = (
                    self.feature_transformer.get_feature_names_out()
                )
            else:
                feature_names_transformed = self.feature_names

            # Generar explicación para cada transacción
            explanations = []

            for tx_idx in range(
                X_transformed.shape[0]
            ):  # Iterar sobre cada transacción
                feature_importance = []

                # Obtener valores SHAP para esta transacción específica
                tx_shap_values = (
                    shap_values[tx_idx] if len(shap_values.shape) > 1 else shap_values
                )

                for feature_idx, (feature_name, shap_val) in enumerate(
                    zip(feature_names_transformed, tx_shap_values)
                ):
                    original_name = feature_name
                    if "__" in feature_name:
                        original_name = (
                            feature_name.split("__")[1]
                            if len(feature_name.split("__")) > 1
                            else feature_name
                        )

                    feature_importance.append(
                        {
                            "feature": original_name,
                            "shap_value": float(shap_val),
                            "impact": (
                                "increases_risk" if shap_val > 0 else "decreases_risk"
                            ),
                            "magnitude": abs(float(shap_val)),
                        }
                    )

                # Ordenar por magnitud (importancia)
                feature_importance.sort(key=lambda x: x["magnitude"], reverse=True)

                # Crear explicación para esta transacción
                tx_explanation = {
                    "top_risk_factors": feature_importance,
                    "base_risk": float(self.explainer.expected_value),
                    "total_features_analyzed": len(feature_importance),
                    "transaction_index": tx_idx,
                }

                explanations.append(tx_explanation)

            return explanations

        except Exception as e:
            print(f"[WARNING] Error generando SHAP: {str(e)}")
            # Retornar lista vacía del mismo tamaño que el número de transacciones
            return [
                {
                    "top_risk_factors": [],
                    "base_risk": 0.0,
                    "total_features_analyzed": 0,
                    "explanation": "No se pudo generar explicación detallada",
                    "error": str(e),
                    "transaction_index": i,
                }
                for i in range(X_transformed.shape[0])
            ]

    def _interpret_risk_level(self, probability: float) -> str:
        """Interpretar nivel de riesgo basado en probabilidad"""

        if probability < 0.1:
            return "LOW"
        elif probability < 0.2:
            return "MEDIUM"
        elif probability < 0.8:
            return "HIGH"
        else:
            return "VERY_HIGH"


def predict_transaction_risk(
    transaction: Dict[str, Any], model_dir: str = None
) -> Dict[str, Any]:
    """Función wrapper para predicción rápida"""
    predictor = TransactionRiskPredictor(model_dir)
    return predictor.predict_risk(transaction)

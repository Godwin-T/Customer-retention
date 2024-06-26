RAW_DATASET = "../data/raw_data/Telco-Customer-Churn.csv"
TARGET_COLUMN = "churn"
DROP_COLUMNS = ["customerid"]
PROCESSED_DATASET = "../data/processed_data/churn.csv"
MODEL_PATH = "../models/churn_model.pkl"
METRICS_PATH = "../model_output/metrics.json"
PREDICTIONS_PATH = "../model_output/predictions.csv"
ROC_CURVE_PATH = "../model_output/roc_curve.csv"
PREDICTION_URL = "http://127.0.0.1:9696/predict"

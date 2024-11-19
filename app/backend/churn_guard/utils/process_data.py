import os
import pandas as pd
from typing import List
from prefect import task, flow
from dotenv import load_dotenv
from app.churn_guard import save_dataframe_to_relational_db

load_dotenv()

db_name = os.getenv("DB_NAME")
db_dir = os.getenv("DB_DIRECTORY")

raw_dataset_path = os.getenv("RAW_DATASET_PATH")
raw_dataset_name = os.getenv("RAW_DATASET_NAME")

processed_dataset_path = os.getenv("PROCESSED_DATASET_PATH")
processed_dataset_name = os.getenv("PROCESSED_DATASET_NAME")


drop_columns = os.getenv("DROP_COLUMNS")
target_column_name = os.getenv("TARGET_COLUMN")


# Load data
@task(name="Load data from path")
def load_dataset(filepath: str):

    dataframe = pd.read_csv(filepath)
    return dataframe


# Prepare Data
@task(name="Process raw data")
def process_dataset(dataframe: pd.DataFrame, target_column_name, drop_cols=None):

    dataframe.columns = dataframe.columns.str.replace(" ", "_").str.lower()

    categorical_col = dataframe.dtypes[dataframe.dtypes == "object"].index.tolist()
    for col in categorical_col:
        dataframe[col] = dataframe[col].str.replace(" ", "_").str.lower()

    # dataframe = dataframe.drop([drop_cols], axis=1)
    dataframe = dataframe[dataframe["totalcharges"] != "_"]
    dataframe["totalcharges"] = dataframe["totalcharges"].astype("float32")
    dataframe[target_column_name] = (dataframe[target_column_name] == "yes").astype(int)

    return dataframe


@flow(name="Data Processing")
def data_processing_pipeline():

    input_data = load_dataset(filepath=raw_dataset_path)
    save_dataframe_to_relational_db(
        tablename=raw_dataset_name, dbprovider="mysql", data=input_data
    )

    churn_data = process_dataset(input_data, target_column_name, drop_cols=drop_columns)
    save_dataframe_to_relational_db(
        tablename=processed_dataset_name, dbprovider="mysql", data=churn_data
    )
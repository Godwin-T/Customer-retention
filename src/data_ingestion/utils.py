import os
import time
import sqlite3
import argparse
import pandas as pd
from datetime import datetime
from pymongo import MongoClient
from typing import Union, Tuple, Optional
from prefect import task
from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.engine.base import Engine

load_dotenv()


def create_mysql_engine() -> Optional[Engine]:
    """Create and return a MySQL connection engine using environment variables or command line arguments."""

    parser = argparse.ArgumentParser(description="Get database credentials")
    parser.add_argument("--host", default=None, help="Database hostname")
    parser.add_argument("--dbname", default=None, help="Database name")
    parser.add_argument("--username", default=None, help="Database username")
    parser.add_argument("--passkey", default=None, help="Database password")

    args = parser.parse_args()

    # Use command line args if provided, otherwise use environment variables
    hostname = args.host or os.getenv("HOSTNAME")
    dbname = args.dbname or os.getenv("DBNAME")
    username = args.username or os.getenv("MYSQL_USERNAME")
    password = args.passkey or os.getenv("MYSQL_PASSWORD")

    # Check if all required parameters are available
    if not all([hostname, dbname, username, password]):
        print("Missing required database connection parameters")
        return None

    connection_string = (
        f"mysql+mysqlconnector://{username}:{password}@{hostname}/{dbname}"
    )
    engine = create_engine(connection_string)

    # Test connection
    try:
        with engine.connect() as connection:
            print("Connection successful!")
            return engine
    except Exception as e:
        print(f"Connection failed: {e}")
        return None


def connect_sqlite(db_path: str) -> sqlite3.Connection:
    """Create and return a SQLite connection."""
    try:
        return sqlite3.connect(db_path)
    except Exception as e:
        print(f"Error connecting to SQLite: {str(e)}")
        raise


def get_engine() -> Tuple[Union[Engine, sqlite3.Connection], str]:
    """Get appropriate database engine based on availability."""
    sql_engine = create_mysql_engine()

    if sql_engine:
        return sql_engine, "mysql"
    else:
        print("Falling back to SQLite database")
        dbname = "local.db"
        return connect_sqlite(dbname), "sqlite"


# Initialize database connection once
db_engine, db_type = get_engine()

# @task(name="Create table")
def create_table(tablename: str, dfpath: str) -> None:
    """Create a new table from CSV data with timestamp."""
    try:
        now = datetime.now()
        formatted_date = now.strftime("%Y-%m-%d")

        df = pd.read_csv(dfpath)
        df["log_time"] = formatted_date

        if db_type == "sqlite":
            df.to_sql(tablename, db_engine, if_exists="fail", index=False)
        else:
            df.to_sql(name=tablename, con=db_engine, if_exists="append", index=False)

        print(f"Successfully created/updated table '{tablename}'")
    except Exception as e:
        print(f"Error creating table: {str(e)}")


# @task(name="Push data to MongoDB")
def push_data_to_mongo(path: str, dbname: str, collection_name: str) -> None:
    """Import CSV data into MongoDB collection with timestamp."""
    try:
        client = MongoClient("localhost", 27017)
        db = client[dbname]
        collection = db[collection_name]

        # Load CSV file into DataFrame
        df = pd.read_csv(path)
        df["log_time"] = time.time()

        # Convert DataFrame to dictionary and insert
        data = df.to_dict(orient="records")
        collection.insert_many(data)

        print(f"Successfully imported data to MongoDB collection '{collection_name}'")
    except Exception as e:
        print(f"Error pushing data to MongoDB: {str(e)}")


# @task(name="Pull data from MongoDB")
def pull_data_from_mongo(dbname: str, collection_name: str) -> list:
    """Retrieve all documents from a MongoDB collection."""
    try:
        client = MongoClient("localhost", 27017)
        db = client[dbname]
        collection = db[collection_name]

        return list(collection.find())
    except Exception as e:
        print(f"Error pulling data from MongoDB: {str(e)}")
        return []


# @task(name="Update MongoDB data")
def update_mongo_collection(dbname: str, collection_name: str, data: dict) -> None:
    """Update the 'Metrics' field in the first document of a collection."""
    try:
        client = MongoClient("localhost", 27017)
        db = client[dbname]
        collection = db[collection_name]

        update = {"$set": {"Metrics": data}}
        result = collection.update_one({}, update)

        if result.matched_count == 0:
            print("No documents found to update")
        else:
            print(f"Successfully updated {result.modified_count} document(s)")
    except Exception as e:
        print(f"Error updating MongoDB collection: {str(e)}")


# @task(name="Push data to database")
def push_data_to_db(
    tablename: str, dfpath: str = None, data: pd.DataFrame = None
) -> None:
    """Save data to the configured database."""
    try:
        now = datetime.now()
        formatted_date = now.strftime("%Y-%m-%d")

        # Load data from file or use provided DataFrame
        if dfpath:
            data = pd.read_csv(dfpath)

        if data is None:
            raise ValueError("Either dfpath or data must be provided")

        data["date"] = formatted_date

        print(db_type)
        if db_type == "sqlite":
            data.to_sql(tablename, db_engine, if_exists="append", index=False)
        else:
            data.to_sql(name=tablename, con=db_engine, if_exists="append", index=False)

        print(f"Successfully pushed data to '{tablename}' table")
    except Exception as e:
        print(f"Error pushing data to database: {str(e)}")


# @task(name="Pull data from database")
def pull_data_from_db(tablename: str) -> Optional[pd.DataFrame]:
    """Retrieve all data from a database table."""
    try:
        query = f"SELECT * FROM {tablename}"

        if db_type == "sqlite":
            return pd.read_sql(query, db_engine)
        else:
            return pd.read_sql(query, con=db_engine)
    except Exception as e:
        print(f"Error pulling data from database: {str(e)}")
        return None


def load_dataframe(filepath: str) -> pd.DataFrame:
    """Load data from CSV file into a DataFrame."""
    try:
        return pd.read_csv(filepath)
    except Exception as e:
        print(f"Error loading dataframe from {filepath}: {str(e)}")
        raise


# @task(name="Process raw data")
def process_dataframe(
    dataframe: pd.DataFrame, target_col: str, drop_cols: list = None
) -> pd.DataFrame:
    """Clean and preprocess the dataframe for analysis."""
    try:
        # Create a copy to avoid modifying the original
        df = dataframe.copy()

        # Clean column names
        df.columns = df.columns.str.replace(" ", "_").str.lower()

        # Clean categorical columns
        categorical_cols = df.select_dtypes(include=["object"]).columns
        for col in categorical_cols:
            df[col] = df[col].str.replace(" ", "_").str.lower()

        # Drop specified columns
        if drop_cols:
            df = df.drop(drop_cols, axis=1)

        # Handle special case for totalcharges
        if "totalcharges" in df.columns:
            df = df[df["totalcharges"] != "_"]
            df["totalcharges"] = df["totalcharges"].astype("float32")

        # Convert target column to binary
        if target_col in df.columns:
            df[target_col] = (df[target_col] == "yes").astype(int)

        return df
    except Exception as e:
        print(f"Error processing dataframe: {str(e)}")
        raise

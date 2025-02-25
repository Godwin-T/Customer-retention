import os
import time
import sqlite3
import argparse
import pandas as pd
from typing import List
from datetime import datetime
from pymongo import MongoClient


from prefect import task
from sqlalchemy import create_engine
from dotenv import load_dotenv


load_dotenv()

try:

    parser = argparse.ArgumentParser(description="To get database credentials")

    parser.add_argument("--host", default="Unknown", help="host name")
    parser.add_argument("--dbname", default="Unknown", help="host name")
    parser.add_argument("--username", default="Unknown", help="host name")
    parser.add_argument("--passkey", default="Unknown", help="host name")

    args = parser.parse_args()

    if args.host == "Unknown":

        dbname = os.getenv("DBNAME")
        username = os.getenv("MYSQL_USERNAME")
        password = os.getenv("MYSQL_PASSWORD")
        hostname = os.getenv("HOSTNAME")
    else:
        dbname = args.dbname
        username = args.userame
        password = args.passkey
        hostname = args.host

    engine = create_engine(
        f"mysql+mysqlconnector://{username}:{password}@{hostname}/{dbname}"
    )

except:
    """"""


# @task(name="Push data to mongodb")
def push_data_tomongo(path, dbname, dbcollection):

    client = MongoClient("localhost", "27017")
    db = client[dbname]
    collection = db[dbcollection]

    # Load CSV file into DataFrame
    df = pd.read_csv(path)
    df["log_time"] = time.time()

    # Convert DataFrame to dictionary
    data = df.to_dict(orient="records")

    # Insert data into MongoDB collection
    collection.insert_many(data)

    print("Data imported successfully!")


# @task(name="Load data from mongodb")
def load_data_from_mongodb(dbname, dbcollection):

    client = MongoClient("localhost", "27017")
    db = client[dbname]
    collection = db[dbcollection]

    data = collection.find()
    return data


# @task(name="Update mongodb data")
def insert_collection_to_mongbdb(dbname, dbcollection, data):

    client = MongoClient("localhost", 27017)
    db = client[dbname]

    collection = db[dbcollection]
    update = {"$set": {"Metrics": data}}
    collection.update_one({}, update)


# @task(name="Push data to sqlite")
def save_dataframe_to_sqlite(db_directory, dbname, tablename, dfpath=None, data=None):

    now = datetime.now()
    formatted_date = now.strftime("%Y-%m-%d")

    if dfpath:

        data = pd.read_csv(dfpath)
        data["date"] = formatted_date

    else:
        data.loc[:, "date"] = formatted_date

    print("==============================================")
    print(db_directory, dbname)
    db_path = os.path.join(db_directory, dbname)
    conn = sqlite3.connect(db_path)

    data.to_sql(tablename, conn, if_exists="append", index=False)
    conn.close()


# @task(name="Push data to sqlite")
def save_dataframe_to_mysql(sql_engine, tablename, dfpath=None, data=None):

    now = datetime.now()
    formatted_date = now.strftime("%Y-%m-%d")

    if dfpath:

        data = pd.read_csv(dfpath)
        data["date"] = formatted_date

    else:
        data["date"] = formatted_date

    # Save the DataFrame to MySQL
    data.to_sql(name=tablename, con=sql_engine, if_exists="append", index=False)


# @task(name="Update sqlite data")
def insert_record(dbname, tablename, record: tuple):

    conn = sqlite3.connect(dbname)
    cursor = conn.cursor()
    cursor.execute(f"INSERT INTO {tablename} {(record)}")

    conn.commit()
    conn.close()


# @task(name="Create sqlite database table")
def create_sqlite_database_table(dbname, tablename, dfpath):

    now = datetime.now()
    formatted_date = now.strftime("%Y-%m-%d")
    df = pd.read_csv(dfpath)
    df["log_time"] = formatted_date

    conn = sqlite3.connect(dbname)
    df.to_sql(tablename, conn, if_exists="fail", index=False)
    conn.close()


# @task(name="Create mysql database table")
def create_mysql_database_table(sql_engine, dfpath, tablename):

    now = datetime.now()
    formatted_date = now.strftime("%Y-%m-%d")

    df = pd.read_csv(dfpath)
    df["log_time"] = formatted_date
    df.to_sql(
        name=tablename, con=sql_engine, if_exists="append", index=False
    )  # Save the DataFrame to MySQL


# @task(name="Load data from sqlite")
def load_data_from_sqlite_db(db_directory, dbname, tablename):

    db_path = os.path.join(db_directory, dbname)
    conn = sqlite3.connect(db_path)
    query = f"SELECT * FROM {tablename}"
    # Load data into a DataFrame
    df = pd.read_sql(query, conn)
    return df


# @task(name="Load data from mysql")
def load_data_from_mysql_db(sql_engine, tablename):

    query = f"SELECT * FROM {tablename}"
    df = pd.read_sql(query, con=sql_engine)
    return df


def save_dataframe_to_relational_db(
    tablename,
    dbprovider="sqlite",
    db_directory=None,
    dbname=None,
    df_path=None,
    data=None,
):

    if dbprovider == "sqlite":

        save_dataframe_to_sqlite(db_directory, dbname, tablename, df_path, data)

    else:

        save_dataframe_to_mysql(engine, tablename, df_path, data)


def load_data_from_relational_db(
    dbprovider="sqlite", db_directory=None, dbname=None, tablename="ProcessedData"
):

    if dbprovider == "sqlite":

        df = load_data_from_sqlite_db(db_directory, dbname, tablename)
    else:
        df = load_data_from_mysql_db(engine, tablename)

    return df


def read_dataset(filepath: str):

    dataframe = pd.read_csv(filepath)
    return dataframe


def prepare_dataset(dataframe: pd.DataFrame, target_col, drop_cols=None):

    dataframe.columns = dataframe.columns.str.replace(" ", "_").str.lower()
    categorical_col = dataframe.dtypes[dataframe.dtypes == "object"].index.tolist()

    for col in categorical_col:
        dataframe[col] = dataframe[col].str.replace(" ", "_").str.lower()

    dataframe = dataframe.drop(drop_cols, axis=1)
    dataframe = dataframe[dataframe["totalcharges"] != "_"]

    dataframe["totalcharges"] = dataframe["totalcharges"].astype("float32")
    dataframe[target_col] = (dataframe[target_col] == "yes").astype(int)

    return dataframe

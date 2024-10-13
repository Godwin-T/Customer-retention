# import mlflow
import os
import boto3
import pickle
import mlflow
import pandas as pd

# from prefect import task, flow
from flask import Flask, request, jsonify
from dotenv import load_dotenv

load_dotenv()


def connect_bucket(access_key_id, access_secret_key):

    s3_bucket = boto3.client(
        "s3", aws_access_key_id=access_key_id, aws_secret_access_key=access_secret_key
    )

    return s3_bucket


# @task
def load_model_from_s3(s3_bucket, bucket_name, file_name):

    obj = s3_bucket.get_object(Bucket=bucket_name, Key=file_name)
    model = obj["Body"].read()
    model = pickle.loads(model)
    return model


# mlflow.set_tracking_uri(MLFLOW_TRACKING_URI)
def load__mlflow_model(model_name, model_stage="Production"):

    model = mlflow.pyfunc.load_model(model_uri=f"models:/{model_name}/{model_stage}")
    return model


# @task


def load_data(data):

    data = pd.DataFrame(data)
    return data


def input_data_processing(data):

    data.drop_duplicates(inplace=True)
    data.columns = data.columns.str.lower()
    data.columns = data.columns.str.replace(" ", "_").str.lower()

    categorical_col = data.dtypes[data.dtypes == "object"].index.tolist()
    for col in categorical_col:
        data[col] = data[col].str.replace(" ", "_").str.lower()
    customer_id = data.pop("customerid")

    return customer_id, data


# @task
def output_data_processing(customer_id, prediction):

    dicts = {"customerid": customer_id, "churn": prediction}
    data_frame = pd.DataFrame(dicts)

    data_frame = data_frame[data_frame["churn"] >= 0.6]
    data_frame["churn"] = data_frame["churn"].astype("int")

    return data_frame


def upload_prediction_to_s3(s3_bucket, local_file_path, bucket_name, s3_object_name):

    s3_bucket.upload_file(local_file_path, bucket_name, s3_object_name)
    return "Object saved successfully"


access_key_id = os.getenv("AWS_SERVER_PUBLIC_KEY")
access_secret_key = os.getenv("AWS_SERVER_SECRET_KEY")
bucket_name = os.getenv("BUCKETNAME")
object_name = os.getenv("OBJECTNAME")

s3_bucket = connect_bucket(access_key_id, access_secret_key)
model = load_model_from_s3(s3_bucket, bucket_name, object_name)


app = Flask("Churn")


@app.route("/predict", methods=["POST"])
# @flow
def predict():

    data = request.get_json()
    # model = load_model(MODEL_NAME, MODEL_STAGE)

    data = load_data(data)
    customer_id, record = input_data_processing(data)
    record = record.to_dict(orient="records")

    prediction = model.predict(record)
    output = output_data_processing(customer_id, prediction)
    output.to_csv("prediction.csv", index=False)
    upload_prediction_to_s3(s3_bucket, "prediction.csv", bucket_name, "prediction.csv")

    return jsonify(
        {"Response": "The predictions have successfully been saved to database"}
    )


if __name__ == "__main__":
    app.run(debug=True, port=9696)

# mlflow.set_tracking_uri(MLFLOW_TRACKING_URI)
# loaded_model = mlflow.pyfunc.load_model(f"models:/{model_name}/{model_stage}")
# mongo_client = MongoClient(MONGODB_ADDRESS)
# db = mongo_client.get_database("prediction_service")
# collection = db.get_collection("data")
# save_to_db(record, bool(prediction))
# send_to_evidently_service(record, bool(prediction))
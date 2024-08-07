# import mlflow
import os
import pickle
import pandas as pd
from utils import BUCKETNAME, OBJECTNAME
from flask import Flask, request, jsonify
from prefect import task, flow
import boto3


# @task
def load_model(bucket_name, file_name):

    s3 = boto3.client(
        "s3",
        aws_access_key_id=os.environ["AWS_SERVER_PUBLIC_KEY"],
        aws_secret_access_key=os.environ["AWS_SERVER_SECRET_KEY"],
    )
    obj = s3.get_object(Bucket=bucket_name, Key=file_name)
    model = obj["Body"].read()
    model = pickle.loads(model)
    return model


# @task
def prepare_data(data):

    data = pd.DataFrame(data)
    data.columns = data.columns.str.lower()

    data.columns = data.columns.str.replace(" ", "_").str.lower()

    categorical_col = data.dtypes[data.dtypes == "object"].index.tolist()
    for col in categorical_col:
        data[col] = data[col].str.replace(" ", "_").str.lower()
    customer_id = data.pop("customerid")

    return customer_id, data


# @task
def prepare_output(customer_id, prediction):

    dicts = {"customerid": customer_id, "churn": prediction}
    data_frame = pd.DataFrame(dicts)

    data_frame = data_frame[data_frame["churn"] >= 0.6]
    churn_proba = data_frame["churn"].tolist()
    customer_id = data_frame["customerid"].tolist()

    prediction = [str(pred) for pred in churn_proba]
    customer_id = [str(id) for id in customer_id]

    output = {"customerid": customer_id, "churn": prediction}
    return output


app = Flask("Churn")


@app.route("/predict", methods=["POST"])
# @flow
def predict():

    data = request.get_json()
    model = load_model(BUCKETNAME, OBJECTNAME)

    customer_id, record = prepare_data(data)
    record = record.to_dict(orient="records")

    prediction = model.predict(record)
    output = prepare_output(customer_id, prediction)

    return jsonify(output)


# if __name__ == "__main__":
#     app.run(debug=True, port = 5080)

# mlflow.set_tracking_uri(MLFLOW_TRACKING_URI)
# loaded_model = mlflow.pyfunc.load_model(f"models:/{model_name}/{model_stage}")
# mongo_client = MongoClient(MONGODB_ADDRESS)
# db = mongo_client.get_database("prediction_service")
# collection = db.get_collection("data")
# save_to_db(record, bool(prediction))
# send_to_evidently_service(record, bool(prediction))

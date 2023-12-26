import os
import json
import pickle
from sklearn.pipeline import make_pipeline
from sklearn.linear_model import LogisticRegression
from sklearn.feature_extraction import DictVectorizer
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score
from utils_and_constants import MODEL_PATH


def eval_metrics(y_true, prediction):

    f1 = f1_score(y_true, prediction)
    metrics = {
        "acc": accuracy_score(y_true, prediction),
        "f1_score": f1,
        "precision": precision_score(y_true, prediction),
        "recall": recall_score(y_true, prediction),
    }
    return metrics


def train_model(train_x, train_y, c_value=71):

    train_x = train_x.to_dict(orient="records")
    lr_pipeline = make_pipeline(
        DictVectorizer(sparse=False), LogisticRegression(C=c_value)
    )

    lr_pipeline.fit(train_x, train_y)
    prediction = lr_pipeline.predict(train_x)
    evaluation_result = eval_metrics(train_y, prediction)

    return lr_pipeline, evaluation_result


def evaluate_model(model, X_test, y_test, float_precision=4):

    X_test = X_test.to_dict(orient="records")
    prediction = model.predict(X_test)
    evaluation_result = eval_metrics(y_test, prediction)

    evaluation_result = json.loads(
        json.dumps(evaluation_result),
        parse_float=lambda x: round(float(x), float_precision),
    )
    return evaluation_result, prediction


def save_model(model):

    if not os.path.exists(os.path.dirname(MODEL_PATH)):
        os.mkdir(os.path.dirname(MODEL_PATH))

    with open(MODEL_PATH, "wb") as f:
        pickle.dump([model], f)
    print("Model saved successfully!")
from app.churn_guard.train_pipeline.train import training_pipeline
from app.churn_guard.utils.deploy import deploy_production

training_pipeline()
# print("Successful")0
result = deploy_production()

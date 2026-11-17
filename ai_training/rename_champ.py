import mlflow
from mlflow import MlflowClient

RUN_ID= "Tangi_yolo26s_2"
NAME= "flexistaff_aqua-team"
client = MlflowClient()

mv = mlflow.register_model(f"runs:/{RUN_ID}/onnx", NAME)
client.set_registered_model_alias(NAME,"champion", mv.version)
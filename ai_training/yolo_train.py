import json
import os
from pathlib import Path
 
import mlflow
import onnx
from ultralytics import YOLO, settings
 
# CONFIG
 
 
ROOT = Path(__file__).resolve().parents[1]
DATASET = ROOT / "dataset/prepared/data.yaml"
 
MODEL_NAME = "yolo26n.pt"
EPOCHS = 100
PATIENCE = 6
BATCH = 4
IMGSZ = 640
RUN_NAME = "Tangi_yolo26n"
 
 
 
with open(os.environ["FLEXISTAFF_CREDENTIALS"], encoding="utf-8") as f:
    creds = json.load(f)["mlflow"]
 
os.environ["MLFLOW_TRACKING_USERNAME"] = creds["username"]
os.environ["MLFLOW_TRACKING_PASSWORD"] = creds["password"]
 
mlflow.set_tracking_uri(creds["tracking_uri"])
 
# Experience commune Team Aqua
experience = mlflow.set_experiment(experiment_id="7")
 
if experience.name != "flexistaff_team-aqua":
    raise ValueError("Mauvaise experience MLflow !")
 
# Suivi MLflow manuel uniquement
settings.update({"mlflow": False})
 
if not DATASET.is_file():
    raise FileNotFoundError(f"Dataset introuvable : {DATASET}")
 
print("Experience :", experience.name)
print("Modele :", MODEL_NAME)
print("Dataset :", DATASET)
 
 
# ENTRAINEMENT YOLO LARGE
 
 
model = YOLO(MODEL_NAME)
 
with mlflow.start_run(run_name=RUN_NAME) as run:
 
    mlflow.set_tags(
        {
            "squad": "team-aqua",
            "dataset": "aqua_v1",
            "membre": "tangi",
            "objectif": "ameliorer_recall",
        }
    )
 
    mlflow.log_params(
        {
            "model": MODEL_NAME,
            "epochs": EPOCHS,
            "imgsz": IMGSZ,
            "batch": BATCH,
            "device": "cuda:0",
            "seed": 42,
            "patience": PATIENCE,
            "degrees": 3.0,
            "translate": 0.03,
            "scale": 0.10,
            "perspective": 0.0002,
            "hsv_v": 0.20,
            "fliplr": 0.0,
            "flipud": 0.0,
            "mosaic": 0.0,
        }
    )
 
    res = model.train(
        data=str(DATASET),
        epochs=EPOCHS,
        imgsz=IMGSZ,
        batch=BATCH,
        device=0,
        seed=42,
        patience=20,
        # DATA AUGMENTATION
        degrees=3.0,
        translate=0.03,
        scale=0.10,
        perspective=0.0002,
        hsv_v=0.20,
        # Pas de retournement du texte
        fliplr=0.0,
        flipud=0.0,
        mosaic=0.0,
        plots=True,
        project=str(ROOT / "runs"),
        name=RUN_NAME,
        exist_ok=False,
    )
 
    # 3 METRIQUES MLFLOW
 
 
    metrics = {
        "recall": float(res.box.mr),
        "precision": float(res.box.mp),
        "mAP50": float(res.box.map50),
    }
 
    # Onglet Metrics
    mlflow.log_metrics(metrics)
 
    # Fichier JSON dans Artifacts
    mlflow.log_dict(metrics, "metrics/summary.json")
 
 
 
    run_dir = Path(model.trainer.save_dir)
 
    # Metriques par epoque
    csv_file = run_dir / "results.csv"
 
    if csv_file.exists():
        mlflow.log_artifact(str(csv_file), artifact_path="metrics")
 
    # Graphiques principaux
    plots = [
        "results.png",
        "confusion_matrix.png",
        "confusion_matrix_normalized.png",
        "BoxPR_curve.png",
        "BoxR_curve.png",
    ]
 
    for filename in plots:
        fichier = run_dir / filename
 
        if fichier.exists():
            mlflow.log_artifact(str(fichier), artifact_path="plots")
 
 
    best_pt = Path(model.trainer.best)
 
    mlflow.log_artifact(str(best_pt), artifact_path="weights")
 
 
 
    onnx_path = YOLO(str(best_pt)).export(format="onnx", imgsz=IMGSZ)
 
    mlflow.log_artifact(str(onnx_path), artifact_path="modeles")
 
    mlflow.onnx.log_model(
        onnx.load(str(onnx_path)), name="onnx", save_as_external_data=False
    )
 
    print("\nEntrainement termine !")
    print("Experience :", experience.name)
    print("Run ID :", run.info.run_id)
    print("Recall :", metrics["recall"])
    print("Precision :", metrics["precision"])
    print("mAP50 :", metrics["mAP50"])
 
 
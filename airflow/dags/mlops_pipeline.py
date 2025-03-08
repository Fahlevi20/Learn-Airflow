from airflow import DAG
from airflow.operators.python import PythonOperator
from datetime import datetime, timedelta
import pandas as pd
import pickle
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score

# Konfigurasi Default DAG
default_args = {
    "owner": "airflow",
    "depends_on_past": False,
    "start_date": datetime(2025, 3, 1),
    "retries": 1,
    "retry_delay": timedelta(minutes=5),
}

# Fungsi: Ingest Data
def ingest_data():
    url = "https://raw.githubusercontent.com/jbrownlee/Datasets/master/pima-indians-diabetes.data.csv"
    col_names = ["Pregnancies", "Glucose", "BloodPressure", "SkinThickness", "Insulin", "BMI", "DiabetesPedigree", "Age", "Outcome"]
    df = pd.read_csv(url, names=col_names)
    df.to_csv("/tmp/data.csv", index=False)
    print("Data successfully ingested!")

# Fungsi: Preprocess Data
def preprocess_data():
    df = pd.read_csv("/tmp/data.csv")
    df.fillna(df.mean(), inplace=True)
    df.to_csv("/tmp/processed_data.csv", index=False)
    print("Data successfully preprocessed!")

# Fungsi: Train Model
def train_model():
    df = pd.read_csv("/tmp/processed_data.csv")
    X = df.drop("Outcome", axis=1)
    y = df["Outcome"]
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
    
    model = RandomForestClassifier(n_estimators=100, random_state=42)
    model.fit(X_train, y_train)
    
    # Simpan model
    with open("/tmp/model.pkl", "wb") as f:
        pickle.dump(model, f)
    
    print("Model successfully trained!")

# Fungsi: Evaluate Model
def evaluate_model():
    df = pd.read_csv("/tmp/processed_data.csv")
    X = df.drop("Outcome", axis=1)
    y = df["Outcome"]
    _, X_test, _, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

    with open("/tmp/model.pkl", "rb") as f:
        model = pickle.load(f)
    
    y_pred = model.predict(X_test)
    acc = accuracy_score(y_test, y_pred)
    
    with open("/tmp/accuracy.txt", "w") as f:
        f.write(str(acc))
    
    print(f"Model accuracy: {acc:.4f}")

# Fungsi: Deploy Model (jika akurasi > 75%)
def deploy_model():
    with open("/tmp/accuracy.txt", "r") as f:
        acc = float(f.read().strip())

    if acc > 0.75:
        print("Model passed evaluation! Deploying...")
        # Simpan model ke lokasi deployment (bisa cloud atau API)
        with open("/tmp/deployed_model.pkl", "wb") as f:
            with open("/tmp/model.pkl", "rb") as model_file:
                f.write(model_file.read())
        print("Model successfully deployed!")
    else:
        print("Model accuracy too low. Deployment aborted.")

# Definisi DAG
dag = DAG(
    "mlops_pipeline",
    default_args=default_args,
    description="MLOps pipeline with Apache Airflow",
    schedule_interval="0 6 * * *",  # Run setiap hari jam 06:00
    catchup=False,
)

# Task Definitions
task_ingest = PythonOperator(task_id="ingest_data", python_callable=ingest_data, dag=dag)
task_preprocess = PythonOperator(task_id="preprocess_data", python_callable=preprocess_data, dag=dag)
task_train = PythonOperator(task_id="train_model", python_callable=train_model, dag=dag)
task_evaluate = PythonOperator(task_id="evaluate_model", python_callable=evaluate_model, dag=dag)
task_deploy = PythonOperator(task_id="deploy_model", python_callable=deploy_model, dag=dag)

# Define Workflow
task_ingest >> task_preprocess >> task_train >> task_evaluate >> task_deploy

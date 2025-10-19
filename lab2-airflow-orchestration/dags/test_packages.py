from airflow import DAG
from airflow.operators.python import PythonOperator
from datetime import datetime

def test_imports():
    print("Testing package imports...")
    
    try:
        import boto3
        print("✅ boto3 works")
    except:
        print("❌ boto3 failed")
    
    try:
        import pandas
        print("✅ pandas works")
    except:
        print("❌ pandas failed")
    
    try:
        import wikipedia
        print("✅ wikipedia works!")
    except ImportError as e:
        print(f"❌ wikipedia failed: {e}")
    
    return "test_complete"

with DAG(
    'test_packages',
    start_date=datetime(2025, 10, 1),
    schedule_interval=None,
    catchup=False,
) as dag:
    
    test = PythonOperator(
        task_id='test_imports',
        python_callable=test_imports,
    )

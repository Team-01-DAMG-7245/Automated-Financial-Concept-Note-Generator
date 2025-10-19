from airflow import DAG
from airflow.operators.python import PythonOperator
from datetime import datetime

def test_everything():
    """Test all packages we need"""
    results = {}
    
    # Test boto3 (AWS SDK)
    try:
        import boto3
        results['boto3'] = "✅ Works"
    except:
        results['boto3'] = "❌ Failed"
    
    # Test pandas
    try:
        import pandas
        results['pandas'] = "✅ Works"
    except:
        results['pandas'] = "❌ Failed"
    
    # Test openai
    try:
        import openai
        results['openai'] = "✅ Works"
    except:
        results['openai'] = "❌ Failed"
    
    # Test pinecone
    try:
        import pinecone
        results['pinecone'] = "✅ Works"
    except:
        results['pinecone'] = "❌ Failed"
    
    # Test wikipedia
    try:
        import wikipedia
        results['wikipedia'] = "✅ Works"
    except:
        results['wikipedia'] = "❌ Failed"
    
    # Test langchain
    try:
        import langchain
        results['langchain'] = "✅ Works"
    except:
        results['langchain'] = "❌ Failed"
    
    print("=== Package Test Results ===")
    for pkg, status in results.items():
        print(f"{pkg}: {status}")
    
    return results

with DAG(
    'test_what_works',
    start_date=datetime(2025, 10, 1),
    schedule_interval=None,
    catchup=False,
) as dag:
    
    PythonOperator(
        task_id='test_all_packages',
        python_callable=test_everything,
    )

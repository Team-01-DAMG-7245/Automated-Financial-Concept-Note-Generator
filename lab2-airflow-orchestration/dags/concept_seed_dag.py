"""
AURELIA - Concept Seeding DAG
Pre-generates concept notes for common financial terms
"""

from airflow import DAG
from airflow.operators.python import PythonOperator
from datetime import datetime, timedelta

default_args = {
    'owner': 'aurelia-team',
    'depends_on_past': False,
    'start_date': datetime(2025, 10, 1),
    'email_on_failure': False,
    'retries': 1,
    'retry_delay': timedelta(minutes=3),
}

FINANCE_CONCEPTS = [
    'Duration',
    'Sharpe Ratio',
    'Black-Scholes',
    'Value at Risk',
    'Beta',
]

def fetch_concept_from_vectordb(concept_name, **context):
    """Query vector DB for concept"""
    print(f"Querying vector DB for: {concept_name}")
    
    # TODO: Implement Pinecone query
    return {"concept": concept_name, "found": False}

def fetch_from_wikipedia(concept_name, **context):
    """Fallback to Wikipedia"""
    import wikipedia
    
    try:
        print(f"Fetching from Wikipedia: {concept_name}")
        summary = wikipedia.summary(concept_name, sentences=3)
        return {
            "concept": concept_name,
            "source": "wikipedia",
            "content": summary
        }
    except Exception as e:
        print(f"Wikipedia error: {e}")
        return None

def generate_structured_note(concept_name, **context):
    """Generate note using instructor"""
    print(f"Generating note for: {concept_name}")
    
    # TODO: Implement instructor-based generation
    note = {
        "concept_name": concept_name,
        "definition": f"Definition of {concept_name}",
        "source": "placeholder"
    }
    
    return note

def store_in_cache(concept_name, **context):
    """Store in S3 cache"""
    print(f"Caching note for: {concept_name}")
    
    # TODO: Store in S3 and/or Postgres
    return {"stored": True}

with DAG(
    'concept_seed_dag',
    default_args=default_args,
    description='Seed concept database with structured notes',
    schedule_interval=None,  # Manual trigger only
    catchup=False,
    tags=['aurelia', 'concept-seeding'],
) as dag:
    
    for concept in FINANCE_CONCEPTS:
        concept_id = concept.replace(" ", "_").replace("-", "_").lower()
        
        fetch_vector = PythonOperator(
            task_id=f'fetch_vector_{concept_id}',
            python_callable=fetch_concept_from_vectordb,
            op_kwargs={'concept_name': concept},
        )
        
        fetch_wiki = PythonOperator(
            task_id=f'fetch_wiki_{concept_id}',
            python_callable=fetch_from_wikipedia,
            op_kwargs={'concept_name': concept},
        )
        
        generate = PythonOperator(
            task_id=f'generate_{concept_id}',
            python_callable=generate_structured_note,
            op_kwargs={'concept_name': concept},
        )
        
        store = PythonOperator(
            task_id=f'store_{concept_id}',
            python_callable=store_in_cache,
            op_kwargs={'concept_name': concept},
        )
        
        [fetch_vector, fetch_wiki] >> generate >> store

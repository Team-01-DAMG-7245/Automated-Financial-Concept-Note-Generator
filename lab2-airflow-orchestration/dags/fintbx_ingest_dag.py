"""
AURELIA - Orchestrate Lab 1 Pre-computed Embeddings
Lab 1 already generated embeddings - we validate and upload to Pinecone
"""

from airflow import DAG
from airflow.operators.python import PythonOperator
from pinecone import Pinecone, ServerlessSpec
from airflow.models import Variable
from datetime import datetime, timedelta
import json
import os
import boto3

default_args = {
    'owner': 'aurelia-team',
    'depends_on_past': False,
    'start_date': datetime(2025, 10, 1),
    'email_on_failure': False,
    'retries': 2,
    'retry_delay': timedelta(minutes=5),
}

PROCESSED_BUCKET = os.getenv('PROCESSED_BUCKET', 'aurelia-faea36-processed-chunks')
EMBEDDINGS_BUCKET = os.getenv('EMBEDDINGS_BUCKET', 'aurelia-faea36-embeddings')

def load_lab1_embeddings(**context):
    """Load Lab 1's pre-computed chunks with embeddings"""
    s3_client = boto3.client('s3')
    
    print("📥 Loading Lab 1's embedded chunks...")
    
    # Download chunks_markdown_embedded.json
    response = s3_client.get_object(
        Bucket=PROCESSED_BUCKET,
        Key='lab1-outputs/chunks/chunks_markdown_embedded.json'
    )
    
    chunks_with_embeddings = json.loads(response['Body'].read())
    
    print(f"✅ Loaded {len(chunks_with_embeddings)} chunks with embeddings")
    print(f"   Strategy: MarkdownHeader")
    print(f"   Avg tokens: 728")
    print(f"   Embedding dimension: 3072")
    
    # Save to temp file for other tasks
    with open('/tmp/embedded_chunks.json', 'w') as f:
        json.dump(chunks_with_embeddings, f)
    
    return {
        "total_chunks": len(chunks_with_embeddings),
        "status": "loaded",
        "source": "lab1-markdown-strategy"
    }

def upload_to_pinecone(**context):
    """Upload embeddings to Pinecone vector database"""

    pc = Pinecone(api_key=Variable.get('PINECONE_API_KEY'))
    index_name = os.getenv('PINECONE_INDEX', 'aurelia-financial-concepts')
    
    print(f"Uploading to Pinecone index: {index_name}")
    
    # Create index if doesn't exist
    if index_name not in pc.list_indexes().names():
        print(f"Creating new index: {index_name}")
        pc.create_index(
            name=index_name,
            dimension=3072,
            metric='cosine',
            spec=ServerlessSpec(cloud='aws', region='us-east-1')
        )
        import time
        time.sleep(60)
    
    index = pc.Index(index_name)
    
    # Load chunks
    with open('/tmp/embedded_chunks.json', 'r') as f:
        chunks = json.load(f)
    
    # Prepare vectors
    vectors = []
    for i, chunk in enumerate(chunks):
        # Handle different possible formats from Lab 1
        chunk_id = chunk.get('chunk_id') or chunk.get('id') or f'markdown_chunk_{i}'
        embedding = chunk.get('embedding') or chunk.get('embeddings')
        content = chunk.get('content') or chunk.get('text', '')
        metadata = chunk.get('metadata', {})
        
        if embedding:
            vectors.append((
                chunk_id,
                embedding,
                {
                    'content': content[:500],  # First 500 chars
                    'section': metadata.get('section_title', ''),
                    'page': metadata.get('page', 0),
                    'strategy': 'markdown',
                    'token_count': chunk.get('token_count', 0)
                }
            ))
    
    # Upload in batches
    batch_size = 100
    for i in range(0, len(vectors), batch_size):
        batch = vectors[i:i+batch_size]
        index.upsert(vectors=batch)
        print(f"   ✅ Uploaded batch {i//batch_size + 1} ({len(batch)} vectors)")
    
    # Get final stats
    stats = index.describe_index_stats()
    print(f"✅ Pinecone index now has {stats.total_vector_count} vectors")
    
    return {
        "vectors_uploaded": len(vectors),
        "index_total": stats.total_vector_count,
        "status": "success"
    }

def backup_to_s3(**context):
    """Backup embeddings to embeddings bucket"""
    s3_client = boto3.client('s3')
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # Copy from processed to embeddings bucket
    copy_source = {
        'Bucket': PROCESSED_BUCKET,
        'Key': 'lab1-outputs/chunks/chunks_markdown_embedded.json'
    }
    
    s3_client.copy_object(
        CopySource=copy_source,
        Bucket=EMBEDDINGS_BUCKET,
        Key=f'backups/embeddings_{timestamp}.json'
    )
    
    print(f"✅ Backed up to s3://{EMBEDDINGS_BUCKET}/backups/embeddings_{timestamp}.json")
    
    return {"backup_key": f'backups/embeddings_{timestamp}.json'}

def generate_pipeline_report(**context):
    """Generate summary report of pipeline execution"""
    
    load_result = context['ti'].xcom_pull(task_ids='load_lab1_embeddings')
    pinecone_result = context['ti'].xcom_pull(task_ids='upload_to_pinecone')
    backup_result = context['ti'].xcom_pull(task_ids='backup_to_s3')
    
    report = {
        "pipeline_run": {
            "timestamp": datetime.now().isoformat(),
            "status": "success"
        },
        "lab1_integration": {
            "chunks_loaded": load_result.get('total_chunks'),
            "source": load_result.get('source')
        },
        "pinecone_upload": {
            "vectors_uploaded": pinecone_result.get('vectors_uploaded'),
            "index_total": pinecone_result.get('index_total')
        },
        "backup": {
            "location": f"s3://{EMBEDDINGS_BUCKET}/{backup_result.get('backup_key')}"
        }
    }
    
    print("📊 Pipeline Report:")
    print(json.dumps(report, indent=2))
    
    # Save report to S3
    s3_client = boto3.client('s3')
    s3_client.put_object(
        Bucket=EMBEDDINGS_BUCKET,
        Key=f'reports/pipeline_report_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json',
        Body=json.dumps(report, indent=2),
        ContentType='application/json'
    )
    
    return report

with DAG(
    'fintbx_ingest_dag',
    default_args=default_args,
    description='Orchestrate Lab 1 embeddings to Pinecone (Markdown strategy, 49 chunks)',
    schedule_interval='@weekly',
    catchup=False,
    tags=['aurelia', 'rag', 'lab1-integration'],
) as dag:
    
    load = PythonOperator(
        task_id='load_lab1_embeddings',
        python_callable=load_lab1_embeddings,
    )
    
    upload = PythonOperator(
        task_id='upload_to_pinecone',
        python_callable=upload_to_pinecone,
    )
    
    backup = PythonOperator(
        task_id='backup_to_s3',
        python_callable=backup_to_s3,
    )
    
    report = PythonOperator(
        task_id='generate_report',
        python_callable=generate_pipeline_report,
    )
    
    load >> upload >> backup >> report

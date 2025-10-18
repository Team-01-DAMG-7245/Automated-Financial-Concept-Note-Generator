#!/bin/bash

set -e

export AWS_PROFILE=aurelia
export AWS_REGION=us-east-1

# Generate random suffix for globally unique bucket names
SUFFIX=${1:-$(openssl rand -hex 3)}

echo "🪣 Creating S3 buckets with suffix: $SUFFIX"
echo ""

# Bucket names
RAW_PDF_BUCKET="aurelia-${SUFFIX}-raw-pdfs"
PROCESSED_BUCKET="aurelia-${SUFFIX}-processed-chunks"
EMBEDDINGS_BUCKET="aurelia-${SUFFIX}-embeddings"
CONCEPT_NOTES_BUCKET="aurelia-${SUFFIX}-concept-notes"
MWAA_BUCKET="aurelia-${SUFFIX}-mwaa"

# Function to create bucket with tags
create_bucket() {
    local bucket_name=$1
    local bucket_purpose=$2
    
    echo "Creating bucket: $bucket_name"
    
    # Create bucket
    aws s3 mb s3://$bucket_name --region $AWS_REGION
    
    # Add tags
    aws s3api put-bucket-tagging \
        --bucket $bucket_name \
        --tagging "TagSet=[{Key=Project,Value=AURELIA},{Key=Lab,Value=Lab2},{Key=Purpose,Value=$bucket_purpose}]"
    
    # Enable versioning for critical buckets
    if [[ "$bucket_purpose" == "raw-pdfs" ]] || [[ "$bucket_purpose" == "mwaa" ]]; then
        aws s3api put-bucket-versioning \
            --bucket $bucket_name \
            --versioning-configuration Status=Enabled
        echo "  ✅ Versioning enabled"
    fi
    
    echo "  ✅ Created: s3://$bucket_name"
    echo ""
}

# Create all buckets
create_bucket $RAW_PDF_BUCKET "raw-pdfs"
create_bucket $PROCESSED_BUCKET "processed-chunks"
create_bucket $EMBEDDINGS_BUCKET "embeddings"
create_bucket $CONCEPT_NOTES_BUCKET "concept-notes"
create_bucket $MWAA_BUCKET "mwaa"

# Create folder structure in MWAA bucket
echo "Creating folder structure in MWAA bucket..."
aws s3api put-object --bucket $MWAA_BUCKET --key dags/
aws s3api put-object --bucket $MWAA_BUCKET --key plugins/
echo "  ✅ MWAA folder structure created"
echo ""

# Save bucket names to config
mkdir -p ../config
cat > ../config/s3_buckets.env << ENVEOF
export RAW_PDF_BUCKET=$RAW_PDF_BUCKET
export PROCESSED_BUCKET=$PROCESSED_BUCKET
export EMBEDDINGS_BUCKET=$EMBEDDINGS_BUCKET
export CONCEPT_NOTES_BUCKET=$CONCEPT_NOTES_BUCKET
export MWAA_BUCKET=$MWAA_BUCKET
export BUCKET_SUFFIX=$SUFFIX
ENVEOF

echo "✅ Bucket configuration saved to config/s3_buckets.env"
echo ""
echo "To use these buckets, run:"
echo "  source config/s3_buckets.env"
echo ""
echo "📊 Summary of created buckets:"
echo "  📄 Raw PDFs:        s3://$RAW_PDF_BUCKET"
echo "  🔄 Processed:       s3://$PROCESSED_BUCKET"
echo "  🧮 Embeddings:      s3://$EMBEDDINGS_BUCKET"
echo "  📝 Concept Notes:   s3://$CONCEPT_NOTES_BUCKET"
echo "  🌪️  MWAA:           s3://$MWAA_BUCKET"
echo ""
echo "Next steps:"
echo "  1. source config/s3_buckets.env"
echo "  2. Upload requirements.txt: aws s3 cp requirements.txt s3://\$MWAA_BUCKET/"

# Lab 2 Deployment Summary

## Created Resources

### IAM
- Group: `aurelia`
- Users: aurelia-dev, teammate1, teammate2
- Policies: AureliaAirflowPolicy, AmazonS3FullAccess, AmazonEC2FullAccess
- Execution Role: AureliaMWAAExecutionRole

### S3 Buckets
- aurelia-3c28b5-raw-pdfs
- aurelia-3c28b5-processed-chunks
- aurelia-3c28b5-embeddings
- aurelia-3c28b5-concept-notes
- aurelia-3c28b5-mwaa

### VPC
- VPC ID: vpc-0d1c7ba4a55536f5d
- Subnets: subnet-07d27f589b82409ac, subnet-0bc2ed133e7543910
- Security Group: sg-0619c3bd1c49e69f0
- NAT Gateways: 2

### MWAA
- Name: aurelia-mwaa
- Status: CREATING (started at [TIME])
- Expected completion: ~30 minutes

## Next Steps
1. Wait for MWAA to be AVAILABLE
2. Deploy DAGs
3. Access Airflow UI
4. Test DAG execution

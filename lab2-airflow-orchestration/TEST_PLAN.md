# Lab 2 Testing Plan

## When MWAA is Available

### 1. Deploy DAGs
```bash
./scripts/deploy_dags.sh
```

### 2. Access Airflow UI
```bash
aws mwaa get-environment --name aurelia-mwaa --query 'Environment.WebserverUrl' --output text
```

### 3. Test DAGs
- [ ] Verify DAGs appear in UI
- [ ] Manually trigger fintbx_ingest_dag
- [ ] Check task logs
- [ ] Verify S3 artifacts created

### 4. Integration with Lab 1
- [ ] Upload actual fintbx.pdf
- [ ] Update DAG to use Lab 1 parser
- [ ] Test end-to-end pipeline

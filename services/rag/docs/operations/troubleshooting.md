# RAG Service Troubleshooting

## Common Issues

### 1. Slow Query Performance

**Symptoms**: Queries taking > 5 seconds
**Solutions**:

- Check vector index exists: `\d+ chunks` in psql
- Rebuild index: `REINDEX INDEX chunks_embedding_idx;`
- Increase maintenance_work_mem in PostgreSQL
- Use pre-filtering to reduce search space

### 2. Low Quality Answers

**Symptoms**: Irrelevant or low-confidence answers
**Solutions**:

- Review chunk size/overlap settings
- Verify embedding model is correct
- Check source document quality
- Tune similarity threshold

### 3. Embedding Generation Failures

**Symptoms**: "Embedding service unavailable"
**Solutions**:

- Check AI Broker health
- Verify AI_BROKER_URL configuration
- Check API quotas
- Enable retry logic

### 4. Out of Memory

**Symptoms**: Container OOMKilled
**Solutions**:

- Increase memory limits
- Reduce batch size for ingestion
- Enable embedding caching
- Review query result size (top_k)

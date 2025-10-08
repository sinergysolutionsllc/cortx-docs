# AI Broker Service Test Plan

## Test Objectives

1. Verify text generation across all providers
2. Ensure embedding generation accuracy
3. Validate PII detection and redaction
4. Test cost tracking and quotas
5. Confirm streaming functionality

## Unit Tests

```python
# test_generation.py
def test_generate_text_with_vertex_ai()
def test_generate_text_with_openai_fallback()
def test_streaming_response()
def test_max_tokens_limit()

# test_embeddings.py
def test_single_text_embedding()
def test_batch_embeddings()
def test_embedding_normalization()

# test_pii.py
def test_detect_ssn()
def test_detect_email()
def test_redact_pii_before_api_call()

# test_cost.py
def test_calculate_token_cost()
def test_quota_enforcement()
```

## Integration Tests

```python
# test_providers.py
def test_vertex_ai_end_to_end()
def test_provider_failover()
def test_streaming_with_real_api()
```

## Performance Targets

| Operation | Target | Acceptable |
|-----------|--------|------------|
| Text Generation | < 2s | < 5s |
| Embeddings | < 500ms | < 1s |
| PII Detection | < 100ms | < 200ms |

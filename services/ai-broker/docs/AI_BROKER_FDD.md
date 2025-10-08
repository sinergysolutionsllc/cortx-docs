# CORTX AI Broker Service - Functional Design Document

**Version**: 1.0.0
**Last Updated**: 2025-10-08
**Status**: Active

## 1. Purpose and Scope

### 1.1 Purpose

The AI Broker service abstracts AI/ML provider interactions, providing a unified interface for text generation, embeddings, and AI-powered features across the CORTX platform.

### 1.2 Scope

- Provider routing (Vertex AI primary, OpenAI/Anthropic fallback)
- Text generation and completion
- Embedding generation for vector search
- PII detection and redaction
- Function calling support
- Streaming response support
- Cost tracking and usage monitoring

### 1.3 Out of Scope

- Training custom models
- Fine-tuning
- Model deployment infrastructure

## 2. Key Features

### 2.1 Multi-Provider Support

- **Vertex AI**: Primary provider (Google Cloud)
  - Models: text-bison, chat-bison, textembedding-gecko
- **OpenAI**: Fallback provider
  - Models: gpt-4, gpt-3.5-turbo, text-embedding-ada-002
- **Anthropic**: Alternative provider
  - Models: claude-3-opus, claude-3-sonnet

### 2.2 Text Generation

- Prompt-based text generation
- Configurable parameters (temperature, top_p, max_tokens)
- Streaming support for real-time responses
- Function calling for structured outputs

### 2.3 Embeddings

- Generate vector embeddings for text
- Batch embedding support
- Normalized vectors for cosine similarity

### 2.4 PII Protection

- Detect PII in prompts (SSN, phone, email, etc.)
- Automatic redaction before sending to providers
- Restore PII in responses if needed

### 2.5 Cost Management

- Track token usage per request
- Provider cost calculation
- Usage quotas and limits
- Cost alerting

## 3. API Contracts

### 3.1 Text Generation

```
POST /v1/generate
Body:
  {
    "prompt": "string",
    "model": "text-bison@002",
    "temperature": 0.7,
    "max_tokens": 1024,
    "stream": false
  }
Response: 200 OK
  {
    "text": "generated text",
    "model": "text-bison@002",
    "usage": {
      "prompt_tokens": 10,
      "completion_tokens": 50,
      "total_tokens": 60
    },
    "cost_usd": 0.002
  }
```

### 3.2 Embeddings

```
POST /v1/embeddings
Body:
  {
    "texts": ["text1", "text2"],
    "model": "textembedding-gecko@003"
  }
Response: 200 OK
  {
    "embeddings": [[0.1, 0.2, ...], [0.3, 0.4, ...]],
    "model": "textembedding-gecko@003",
    "dimensions": 768
  }
```

### 3.3 PII Detection

```
POST /v1/pii/detect
Body:
  {
    "text": "My SSN is 123-45-6789"
  }
Response: 200 OK
  {
    "pii_found": true,
    "entities": [
      {
        "type": "SSN",
        "text": "123-45-6789",
        "start": 10,
        "end": 21
      }
    ]
  }
```

## 4. Dependencies

### 4.1 Upstream Dependencies

- **Vertex AI**: Primary AI provider
- **OpenAI API**: Fallback provider (optional)
- **Anthropic API**: Alternative provider (optional)

### 4.2 Downstream Consumers

- **RAG Service**: Embedding generation
- **Validation Service**: AI-powered validation
- **Gateway Service**: Explanation generation
- **Compliance Service**: Document analysis

## 5. Data Models

### 5.1 Generation Request

```python
@dataclass
class GenerationRequest:
    prompt: str
    model: str = "text-bison@002"
    temperature: float = 0.7
    max_tokens: int = 1024
    top_p: float = 1.0
    stream: bool = False
    stop_sequences: Optional[List[str]] = None
```

### 5.2 Embedding Request

```python
@dataclass
class EmbeddingRequest:
    texts: List[str]
    model: str = "textembedding-gecko@003"
    normalize: bool = True
```

### 5.3 Usage Metrics

```python
@dataclass
class UsageMetrics:
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int
    cost_usd: float
    provider: str
    model: str
    timestamp: datetime
```

## 6. Configuration

### 6.1 Environment Variables

| Variable | Type | Default | Description |
|----------|------|---------|-------------|
| `VERTEX_PROJECT_ID` | string | Required | GCP project for Vertex AI |
| `VERTEX_LOCATION` | string | us-central1 | Vertex AI region |
| `OPENAI_API_KEY` | string | Optional | OpenAI API key |
| `ANTHROPIC_API_KEY` | string | Optional | Anthropic API key |
| `DEFAULT_PROVIDER` | string | vertex | Primary provider |
| `ENABLE_PII_DETECTION` | bool | true | Enable PII detection |
| `MAX_TOKENS_PER_REQUEST` | int | 4096 | Max tokens per request |

### 6.2 Provider Configuration

```yaml
providers:
  vertex:
    enabled: true
    models:
      - text-bison@002
      - chat-bison@002
      - textembedding-gecko@003
    cost_per_1k_tokens: 0.001
  openai:
    enabled: false
    models:
      - gpt-4
      - gpt-3.5-turbo
    cost_per_1k_tokens: 0.03
```

## 7. Security Considerations

### 7.1 API Key Management

- Keys stored in Secret Manager
- No keys in code or logs
- Automatic key rotation

### 7.2 PII Protection

- Detect and redact PII before external API calls
- Audit log of redacted content
- Restore PII only in secure contexts

### 7.3 Rate Limiting

- Per-tenant rate limits
- Per-model rate limits
- Graceful degradation on quota exhaustion

### 7.4 Input Validation

- Maximum prompt length (10K characters)
- Malicious input detection
- SQL injection prevention

## 8. Performance Characteristics

### 8.1 Latency Targets

- Text generation: < 2000ms (non-streaming)
- Embeddings: < 500ms per batch
- PII detection: < 100ms

### 8.2 Throughput Targets

- 100 generation requests/second
- 500 embedding requests/second

### 8.3 Resource Requirements

- CPU: 1 core baseline, 4 cores under load
- Memory: 512MB baseline, 2GB under load

## 9. Monitoring and Observability

### 9.1 Metrics

- Request count by provider and model
- Token usage and cost
- Latency (p50, p95, p99)
- Error rate by provider
- PII detection rate

### 9.2 Alerts

- Provider API errors > 5%
- Cost exceeds budget threshold
- Rate limit exhaustion
- PII detected in production prompts

### 9.3 Logging

- All AI requests logged (prompts sanitized)
- Cost tracking per request
- Provider responses (truncated)

## 10. Future Enhancements

- Custom model deployment
- Fine-tuning support
- Multi-modal support (images, audio)
- Caching of repeated prompts
- Batch processing optimization

## 11. Change Log

| Version | Date | Changes |
|---------|------|---------|
| 1.0.0 | 2025-10-08 | Initial FDD creation |

## 12. References

- [Vertex AI Documentation](https://cloud.google.com/vertex-ai/docs)
- [OpenAI API Reference](https://platform.openai.com/docs/api-reference)
- [Anthropic Claude Documentation](https://docs.anthropic.com/)

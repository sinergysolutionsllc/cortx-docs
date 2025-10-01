# AI Model Selection & Routing Strategy

**Version:** 1.0.0
**Last Updated:** 2025-10-01
**Owner:** AI Platform Team
**Classification:** Internal

---

## Purpose

This document defines the strategy for selecting, routing, and managing AI models across the CORTX Platform. It establishes criteria for model selection based on use case, cost, latency, quality, and compliance requirements.

---

## Model Inventory

### Currently Supported

#### Google Gemini 1.5 Flash
**Provider:** Google Cloud Vertex AI
**Status:** ✅ Production (Default)

**Specifications:**
- **Context Window:** 1M tokens
- **Output Limit:** 8,192 tokens
- **Latency:** p50: 250ms, p95: 500ms, p99: 800ms
- **Cost:** $0.00001875/1K input tokens, $0.000075/1K output tokens
- **Strengths:** Fast, cost-effective, good for routine tasks
- **Limitations:** Lower reasoning quality for complex tasks

**Use Cases:**
- RulePack validation explanations
- Simple Q&A (platform documentation)
- Quick compliance lookups
- Pack template generation
- Basic code suggestions

**Configuration:**
```python
GEMINI_FLASH_CONFIG = {
    "model": "gemini-1.5-flash",
    "temperature": 0.0,  # Deterministic for reproducibility
    "top_p": 0.95,
    "top_k": 40,
    "max_output_tokens": 2048,
    "safety_settings": {
        "HARM_CATEGORY_HATE_SPEECH": "BLOCK_MEDIUM_AND_ABOVE",
        "HARM_CATEGORY_DANGEROUS_CONTENT": "BLOCK_MEDIUM_AND_ABOVE",
        "HARM_CATEGORY_SEXUALLY_EXPLICIT": "BLOCK_MEDIUM_AND_ABOVE",
        "HARM_CATEGORY_HARASSMENT": "BLOCK_MEDIUM_AND_ABOVE"
    }
}
```

#### Google Gemini 1.5 Pro
**Provider:** Google Cloud Vertex AI
**Status:** ✅ Production (Premium)

**Specifications:**
- **Context Window:** 1M tokens
- **Output Limit:** 8,192 tokens
- **Latency:** p50: 600ms, p95: 1200ms, p99: 1800ms
- **Cost:** $0.000125/1K input tokens, $0.000375/1K output tokens
- **Strengths:** Higher quality reasoning, complex tasks
- **Limitations:** Higher cost, slower

**Use Cases:**
- Complex WorkflowPack generation
- Multi-step reasoning tasks
- Advanced code generation
- Compliance policy analysis
- AI-assisted workflow design

**Configuration:**
```python
GEMINI_PRO_CONFIG = {
    "model": "gemini-1.5-pro",
    "temperature": 0.2,  # Slight creativity for complex tasks
    "top_p": 0.95,
    "top_k": 40,
    "max_output_tokens": 4096,
    "safety_settings": {
        "HARM_CATEGORY_HATE_SPEECH": "BLOCK_MEDIUM_AND_ABOVE",
        "HARM_CATEGORY_DANGEROUS_CONTENT": "BLOCK_MEDIUM_AND_ABOVE",
        "HARM_CATEGORY_SEXUALLY_EXPLICIT": "BLOCK_MEDIUM_AND_ABOVE",
        "HARM_CATEGORY_HARASSMENT": "BLOCK_MEDIUM_AND_ABOVE"
    }
}
```

### Planned (Q1-Q2 2026)

#### Anthropic Claude 3.5 Sonnet
**Provider:** Anthropic API
**Status:** 📋 Planned Q1 2026

**Specifications:**
- **Context Window:** 200K tokens
- **Output Limit:** 4,096 tokens
- **Latency (estimated):** p50: 800ms, p95: 1500ms, p99: 2200ms
- **Cost:** $0.003/1K input tokens, $0.015/1K output tokens
- **Strengths:** Highest quality code generation, superior reasoning
- **Limitations:** Highest cost, smaller context window

**Planned Use Cases:**
- Production-quality code generation
- Complex compliance reasoning
- Critical decision support
- High-stakes workflow design
- Architecture recommendations

#### OpenAI GPT-4 Turbo
**Provider:** OpenAI API
**Status:** 📋 Planned Q2 2026

**Specifications:**
- **Context Window:** 128K tokens
- **Output Limit:** 4,096 tokens
- **Latency (estimated):** p50: 700ms, p95: 1400ms, p99: 2000ms
- **Cost:** $0.01/1K input tokens, $0.03/1K output tokens
- **Strengths:** Strong general reasoning, good tool use
- **Limitations:** Higher cost

**Planned Use Cases:**
- Advanced reasoning tasks
- Multi-modal analysis (if needed)
- Complex data analysis
- Enterprise customer preference

#### AWS Bedrock (Claude, Titan)
**Provider:** AWS Bedrock
**Status:** 🔮 Roadmap (Phase 3)

**Rationale:** Enterprise customers requiring AWS infrastructure
**Models:** Claude 3 family, Amazon Titan
**Benefits:** AWS ecosystem integration, enterprise SLAs

### Future Considerations

#### Hugging Face Hosted Models
**Status:** 🔮 Research

**Candidates:**
- `mistralai/Mixtral-8x7B-Instruct-v0.1`
- `meta-llama/Llama-3-70B-Instruct`
- `google/flan-t5-xxl`

**Benefits:** Open source, lower cost, customizable
**Challenges:** Quality variability, hosting complexity

#### On-Premises Models
**Status:** 🔮 Phase 4 (2027+)

**Use Case:** Air-gapped government deployments
**Requirements:** GPU infrastructure, model serving platform
**Candidates:** Llama 3, Mixtral, custom fine-tuned models

---

## Model Routing Strategy

### Decision Tree

```python
async def select_model(
    task_type: str,
    complexity: str,
    latency_requirement: str,
    cost_sensitivity: str,
    tenant_preferences: dict
) -> str:
    """Select optimal model based on task characteristics.

    Args:
        task_type: Type of task (e.g., "code_generation", "explanation", "qa")
        complexity: Task complexity ("simple", "moderate", "complex")
        latency_requirement: Latency tolerance ("low", "medium", "high")
        cost_sensitivity: Cost consideration ("low", "medium", "high")
        tenant_preferences: Tenant-specific model preferences

    Returns:
        Model identifier (e.g., "gemini-1.5-flash")
    """
    # 1. Check tenant preferences (enterprise customers may specify)
    if tenant_preferences.get("preferred_model"):
        return tenant_preferences["preferred_model"]

    # 2. Apply routing rules
    if task_type == "code_generation" and complexity == "complex":
        return "claude-3.5-sonnet"  # Highest quality code
    elif task_type == "explanation" and complexity == "simple":
        return "gemini-1.5-flash"  # Fast, cost-effective
    elif task_type == "workflow_design" and complexity in ["moderate", "complex"]:
        return "gemini-1.5-pro"  # Good balance
    elif latency_requirement == "low" and cost_sensitivity == "high":
        return "gemini-1.5-flash"  # Fastest, cheapest
    elif complexity == "complex" and cost_sensitivity == "low":
        return "claude-3.5-sonnet"  # Best quality
    else:
        return "gemini-1.5-pro"  # Default production model

    # Default fallback
    return "gemini-1.5-flash"
```

### Routing Rules

#### By Task Type

| Task Type | Simple | Moderate | Complex |
|-----------|--------|----------|---------|
| **Code Generation** | Gemini Flash | Gemini Pro | Claude Sonnet |
| **Explanation** | Gemini Flash | Gemini Flash | Gemini Pro |
| **Q&A** | Gemini Flash | Gemini Flash | Gemini Pro |
| **Workflow Design** | Gemini Flash | Gemini Pro | Claude Sonnet |
| **Compliance Analysis** | Gemini Flash | Gemini Pro | Claude Sonnet |
| **Data Analysis** | Gemini Flash | Gemini Pro | GPT-4 Turbo |

#### By Latency Requirement

| Requirement | Model Choice | Max Latency (p99) |
|-------------|--------------|-------------------|
| **Low** (<500ms) | Gemini Flash | 800ms |
| **Medium** (<1500ms) | Gemini Pro | 1800ms |
| **High** (>1500ms) | Claude Sonnet | 2200ms |

#### By Cost Sensitivity

| Sensitivity | Model Choice | Cost/1M Tokens (Input) |
|-------------|--------------|------------------------|
| **High** (minimize cost) | Gemini Flash | $18.75 |
| **Medium** (balance) | Gemini Pro | $125 |
| **Low** (maximize quality) | Claude Sonnet | $3,000 |

---

## Prompt Templates

### Template Structure

```python
from typing import Dict, List

class PromptTemplate:
    """Structured prompt template with variables."""

    def __init__(
        self,
        template_id: str,
        system_prompt: str,
        user_prompt_template: str,
        variables: List[str],
        recommended_model: str,
        temperature: float = 0.0
    ):
        self.template_id = template_id
        self.system_prompt = system_prompt
        self.user_prompt_template = user_prompt_template
        self.variables = variables
        self.recommended_model = recommended_model
        self.temperature = temperature

    def render(self, **kwargs) -> Dict[str, str]:
        """Render template with provided variables."""
        missing = set(self.variables) - set(kwargs.keys())
        if missing:
            raise ValueError(f"Missing required variables: {missing}")

        user_prompt = self.user_prompt_template.format(**kwargs)

        return {
            "system_prompt": self.system_prompt,
            "user_prompt": user_prompt,
            "model": self.recommended_model,
            "temperature": self.temperature
        }
```

### Template Library

#### RulePack Validation Explanation
```python
RULEPACK_EXPLANATION_TEMPLATE = PromptTemplate(
    template_id="rulepack_explanation_v1",
    system_prompt="""You are a compliance expert assistant for the CORTX Platform.
Your role is to explain RulePack validation failures in plain language, referencing
the relevant regulatory requirements and suggesting corrections.

Use the provided RAG context about compliance frameworks.
Be specific, actionable, and cite regulatory codes when applicable.""",

    user_prompt_template="""Explain this validation failure:

**Rule ID:** {rule_id}
**Field:** {field}
**Failed Value:** {failed_value}
**Error Message:** {error_message}

**Compliance Context:**
{rag_context}

Provide:
1. What went wrong (plain language)
2. Why this rule exists (regulatory requirement)
3. How to fix it (specific steps)""",

    variables=["rule_id", "field", "failed_value", "error_message", "rag_context"],
    recommended_model="gemini-1.5-flash",
    temperature=0.0
)
```

#### WorkflowPack Generation
```python
WORKFLOW_GENERATION_TEMPLATE = PromptTemplate(
    template_id="workflow_generation_v1",
    system_prompt="""You are a workflow design expert for the CORTX Platform.
You create WorkflowPacks (YAML) from natural language descriptions.

Follow the WorkflowPack schema strictly. Use appropriate node types:
- data-source: Ingest data
- validation: Execute RulePack
- calculation: Perform computations
- decision: Conditional branching
- approval: Human-in-the-loop
- ai-inference: AI model calls
- data-sink: Output results

Ensure compliance with regulatory frameworks when applicable.""",

    user_prompt_template="""Create a WorkflowPack for this requirement:

**Description:** {description}

**Compliance Requirements:** {compliance_requirements}

**Available RulePacks:** {available_rulepacks}

**RAG Context:**
{rag_context}

Generate a complete WorkflowPack YAML following the schema.
Include metadata, steps with appropriate types, and configurations.""",

    variables=["description", "compliance_requirements", "available_rulepacks", "rag_context"],
    recommended_model="gemini-1.5-pro",
    temperature=0.2
)
```

#### Code Generation
```python
CODE_GENERATION_TEMPLATE = PromptTemplate(
    template_id="code_generation_v1",
    system_prompt="""You are an expert Python/TypeScript developer for the CORTX Platform.

Follow these strict rules:
- Use type hints (Python) or TypeScript strict mode
- Include comprehensive error handling
- Add unit tests for all functions
- Follow PEP 8 (Python) or Airbnb style (TypeScript)
- Include docstrings with examples
- Implement proper logging with correlation IDs
- Never include secrets or hardcoded credentials
- Use parameterized queries (no SQL injection)

All code must be production-ready with >80% test coverage.""",

    user_prompt_template="""Generate {language} code for this requirement:

**Requirement:** {requirement}

**Context:**
{context}

**Constraints:**
{constraints}

**Expected Inputs/Outputs:**
{inputs_outputs}

Provide:
1. Implementation code with type hints
2. Unit tests with fixtures
3. Usage example
4. Brief explanation of design decisions""",

    variables=["language", "requirement", "context", "constraints", "inputs_outputs"],
    recommended_model="claude-3.5-sonnet",  # Best for code
    temperature=0.0
)
```

#### Compliance Q&A
```python
COMPLIANCE_QA_TEMPLATE = PromptTemplate(
    template_id="compliance_qa_v1",
    system_prompt="""You are a regulatory compliance expert for federal, healthcare,
and cybersecurity frameworks (FedRAMP, HIPAA, NIST 800-53, SOC 2).

Answer questions accurately using the provided RAG context.
Cite specific control numbers or regulatory sections.
If uncertain, say so rather than guessing.""",

    user_prompt_template="""Question: {question}

**RAG Context:**
{rag_context}

**Relevant Frameworks:** {frameworks}

Provide a detailed answer with:
1. Direct answer
2. Supporting regulatory citations
3. Implementation guidance (if applicable)
4. Related considerations""",

    variables=["question", "rag_context", "frameworks"],
    recommended_model="gemini-1.5-flash",
    temperature=0.0
)
```

---

## Quality Controls

### Reproducibility

**Requirement:** Same input → same output (>95% consistency)

**Implementation:**
```python
# Use temperature=0 for deterministic tasks
async def get_deterministic_response(
    prompt: str,
    model: str = "gemini-1.5-flash"
):
    response = await llm.generate(
        model=model,
        prompt=prompt,
        temperature=0.0,  # No randomness
        top_p=1.0,        # Full probability mass
        seed=42           # Fixed seed (if supported)
    )
    return response
```

**Testing:**
```python
async def test_reproducibility():
    prompt = "Explain HIPAA Security Rule §164.312(a)(1)"

    responses = []
    for _ in range(10):
        response = await get_deterministic_response(prompt)
        responses.append(response)

    # All responses should be identical
    assert len(set(responses)) == 1, "Responses are not reproducible"
```

### Output Validation

**Requirement:** Validate all AI-generated content before use

**Schema Validation:**
```python
from pydantic import BaseModel, validator

class WorkflowPackOutput(BaseModel):
    """Validate AI-generated WorkflowPack."""
    workflow_id: str
    version: str
    steps: List[dict]

    @validator('version')
    def validate_version(cls, v):
        # Ensure semantic versioning
        if not re.match(r'^\d+\.\d+\.\d+$', v):
            raise ValueError("Invalid version format")
        return v

    @validator('steps')
    def validate_steps(cls, v):
        # Ensure at least one step
        if len(v) < 1:
            raise ValueError("WorkflowPack must have at least one step")
        return v

async def validate_generated_workflow(ai_output: str) -> WorkflowPackOutput:
    """Validate AI-generated WorkflowPack."""
    try:
        workflow_data = yaml.safe_load(ai_output)
        validated = WorkflowPackOutput(**workflow_data)
        return validated
    except Exception as e:
        logger.error("workflow.validation.failed", error=str(e))
        raise
```

### Hallucination Detection

**Requirement:** Detect and flag potentially hallucinated information

**Strategies:**
1. **RAG Citation Check:** Ensure claims are grounded in retrieved context
2. **Fact Verification:** Cross-reference with knowledge base
3. **Confidence Scoring:** Track model confidence (if available)
4. **Human Review:** Flag low-confidence responses for review

```python
def detect_hallucination(
    response: str,
    rag_context: List[str],
    confidence_threshold: float = 0.7
) -> bool:
    """Detect potential hallucinations in AI response.

    Returns:
        True if potential hallucination detected, False otherwise
    """
    # 1. Check if key claims are in RAG context
    response_claims = extract_claims(response)

    grounded_claims = 0
    for claim in response_claims:
        if any(is_claim_in_context(claim, ctx) for ctx in rag_context):
            grounded_claims += 1

    grounding_ratio = grounded_claims / len(response_claims)

    # 2. Flag if <70% of claims are grounded
    if grounding_ratio < confidence_threshold:
        logger.warning(
            "hallucination.detected",
            grounding_ratio=grounding_ratio,
            response_preview=response[:200]
        )
        return True

    return False
```

---

## Cost Management

### Budget Tracking

**Per-Tenant Budget:** Track AI costs by tenant
**Monthly Limit:** Alert at 80% of budget, block at 100%

```python
from datetime import datetime, timedelta

async def track_ai_cost(
    tenant_id: str,
    model: str,
    input_tokens: int,
    output_tokens: int
):
    """Track AI costs per tenant."""
    # Get model pricing
    pricing = MODEL_PRICING[model]

    cost = (
        (input_tokens / 1000) * pricing["input"] +
        (output_tokens / 1000) * pricing["output"]
    )

    # Update tenant usage
    await db.execute(
        """
        INSERT INTO ai_usage (tenant_id, model, cost, tokens_in, tokens_out, timestamp)
        VALUES (:tenant_id, :model, :cost, :tokens_in, :tokens_out, :timestamp)
        """,
        {
            "tenant_id": tenant_id,
            "model": model,
            "cost": cost,
            "tokens_in": input_tokens,
            "tokens_out": output_tokens,
            "timestamp": datetime.utcnow()
        }
    )

    # Check budget
    month_start = datetime.utcnow().replace(day=1, hour=0, minute=0, second=0)
    monthly_cost = await db.fetch_val(
        """
        SELECT SUM(cost) FROM ai_usage
        WHERE tenant_id = :tenant_id AND timestamp >= :month_start
        """,
        {"tenant_id": tenant_id, "month_start": month_start}
    )

    budget_limit = await get_tenant_ai_budget(tenant_id)

    if monthly_cost >= budget_limit * 0.8:
        await alert_budget_threshold(tenant_id, monthly_cost, budget_limit)

    if monthly_cost >= budget_limit:
        raise BudgetExceededError(f"Monthly AI budget exceeded for {tenant_id}")
```

### Model Pricing

```python
MODEL_PRICING = {
    "gemini-1.5-flash": {
        "input": 0.00001875,   # per 1K tokens
        "output": 0.000075
    },
    "gemini-1.5-pro": {
        "input": 0.000125,
        "output": 0.000375
    },
    "claude-3.5-sonnet": {
        "input": 0.003,
        "output": 0.015
    },
    "gpt-4-turbo": {
        "input": 0.01,
        "output": 0.03
    }
}
```

### Cost Optimization

**Strategies:**
1. **Caching:** Cache common responses (1-hour TTL)
2. **Prompt Compression:** Remove unnecessary tokens
3. **Model Downgrading:** Use cheaper models when appropriate
4. **Batch Processing:** Combine multiple requests

```python
async def optimize_cost(
    task_type: str,
    complexity: str,
    cached_result_available: bool
):
    """Optimize cost by selecting cheapest adequate model."""
    if cached_result_available:
        return "cache"  # No cost

    if task_type in ["explanation", "qa"] and complexity == "simple":
        return "gemini-1.5-flash"  # Cheapest

    if complexity == "moderate":
        return "gemini-1.5-pro"  # Mid-tier

    return "gemini-1.5-pro"  # Default (don't auto-select most expensive)
```

---

## Monitoring & Alerting

### Key Metrics

**Usage Metrics:**
- Requests per model (per tenant, per task type)
- Token consumption (input, output)
- Cost per tenant (daily, monthly)
- Model latency (p50, p95, p99)

**Quality Metrics:**
- Error rate by model
- Validation failures (schema, hallucination)
- User feedback (thumbs up/down)
- Reproducibility score

**System Metrics:**
- Model availability
- Rate limit violations
- Cache hit rate
- Retry rate

### Dashboards

```python
# Grafana dashboard configuration
DASHBOARDS = {
    "ai_usage": {
        "requests_by_model": "sum(ai.request.count) by (model)",
        "cost_by_tenant": "sum(ai.cost) by (tenant_id)",
        "latency_by_model": "histogram(ai.request.latency) by (model)",
        "error_rate": "sum(ai.request.errors) / sum(ai.request.count)"
    },
    "quality": {
        "validation_failures": "sum(ai.output.validation_failed)",
        "hallucination_detections": "sum(ai.hallucination.detected)",
        "user_feedback_positive": "sum(ai.feedback.positive) / sum(ai.feedback.total)"
    }
}
```

### Alerts

**Critical:**
- Model unavailable for >5 minutes
- Error rate >5% (any model)
- Budget exceeded for any tenant

**Warning:**
- Model latency p99 >2x baseline
- Hallucination detection rate >10%
- Cache hit rate <50%

```python
ALERTS = {
    "model_unavailable": {
        "condition": "ai.model.available == 0",
        "duration": "5m",
        "severity": "critical",
        "action": "page_oncall"
    },
    "high_error_rate": {
        "condition": "ai.request.errors / ai.request.count > 0.05",
        "duration": "10m",
        "severity": "critical",
        "action": "slack_alert"
    },
    "budget_warning": {
        "condition": "ai.cost.monthly > budget * 0.8",
        "duration": "1m",
        "severity": "warning",
        "action": "email_admin"
    }
}
```

---

## Fallback & Resilience

### Model Fallback Chain

```python
MODEL_FALLBACK_CHAIN = {
    "claude-3.5-sonnet": ["gemini-1.5-pro", "gemini-1.5-flash"],
    "gpt-4-turbo": ["gemini-1.5-pro", "gemini-1.5-flash"],
    "gemini-1.5-pro": ["gemini-1.5-flash"],
    "gemini-1.5-flash": []  # No fallback
}

async def call_with_fallback(
    prompt: str,
    primary_model: str,
    max_retries: int = 3
):
    """Call AI model with automatic fallback."""
    models_to_try = [primary_model] + MODEL_FALLBACK_CHAIN.get(primary_model, [])

    for model in models_to_try:
        try:
            response = await llm.generate(
                model=model,
                prompt=prompt,
                timeout=10  # 10 second timeout
            )
            return response
        except Exception as e:
            logger.warning(
                "model.call.failed",
                model=model,
                error=str(e)
            )
            continue

    raise ModelUnavailableError("All models failed")
```

### Circuit Breaker

```python
from circuitbreaker import circuit

@circuit(failure_threshold=5, recovery_timeout=60)
async def call_llm(model: str, prompt: str):
    """Call LLM with circuit breaker pattern."""
    response = await llm_client.generate(model, prompt)
    return response
```

---

## Compliance & Governance

### Model Approval Process

**New Model Integration:**
1. **Security Review:** Assess data handling, privacy, encryption
2. **Compliance Review:** Verify alignment with FedRAMP, HIPAA, SOC 2
3. **Cost Analysis:** Estimate monthly costs, ROI
4. **Quality Testing:** Benchmark on standard test sets
5. **Pilot Testing:** Limited rollout to select tenants
6. **Production Approval:** Final approval from architecture team

### Data Handling

**PII Protection:**
- All input must be PII-redacted before LLM calls
- No PII in model training data (use commercial APIs only)
- Audit all prompts containing sensitive data

**Data Retention:**
- Prompts: 90 days (for debugging)
- Responses: 30 days (for caching)
- Usage logs: 1 year (for billing)
- Audit logs: 7 years (compliance requirement)

---

## Changelog

**2025-10-01:**
- Initial model selection strategy
- Defined routing rules and templates
- Configured Gemini 1.5 Flash/Pro as primary models
- Planned Claude and GPT-4 integration (Q1-Q2 2026)

---

## Contact

**AI Model Strategy:**
- AI Platform Team: ai-platform@sinergysolutions.ai
- Slack: #ai-model-selection

**Request New Model:**
- Create GitHub issue with `ai-model-request` label
- Include use case, expected cost, and compliance considerations

---

**Document Control**
- **Version:** 1.0.0
- **Last Updated:** 2025-10-01
- **Review Cycle:** Quarterly
- **Next Review:** 2026-01-01
- **Approvers:** AI Platform Team + Architecture Team

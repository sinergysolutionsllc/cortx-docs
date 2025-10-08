# CORTX RulePack SDK

The CORTX RulePack SDK provides a standardized framework for building domain-specific validation containers that integrate with the CORTX orchestration layer.

## Overview

RulePacks are modular validation engines that implement domain-specific business rules while maintaining a consistent interface. Each vertical (FedSuite, ClaimSuite, etc.) can build their own RulePacks without duplicating orchestration logic.

## Key Features

- **Standardized Contract**: All RulePacks implement the same interface
- **Multiple Validation Modes**: Static JSON rules, Hybrid (JSON + AI), and Agentic (AI-first)
- **Built-in Testing**: Comprehensive test utilities for RulePack validation
- **Registry Integration**: Automatic registration and discovery
- **Streaming Support**: Process large datasets efficiently
- **Health Monitoring**: Built-in health check and metrics

## Quick Start

### 1. Install the SDK

```bash
cd /Users/michael/Development/cortx/packages/cortx_rulepack_sdk
pip install -e .
```

### 2. Create Your RulePack

```python
from cortx_rulepack_sdk.base import RulePackBase
from cortx_rulepack_sdk.contracts import *

class MyRulePack(RulePackBase):
    async def validate(self, request: ValidationRequest) -> ValidationResponse:
        # Implement your validation logic
        pass
    
    async def get_info(self) -> RulePackInfo:
        return RulePackInfo(
            domain="my_domain",
            name="MyRulePack", 
            version="1.0.0",
            rule_count=10,
            categories=["business", "format"],
            supported_modes=[ValidationMode.STATIC],
            capabilities=["validate", "explain"]
        )
    
    async def get_metadata(self) -> RulePackMetadata:
        # Return detailed metadata
        pass
```

### 3. Test Your RulePack

```python
from cortx_rulepack_sdk.testing import run_rulepack_tests

# Run contract compliance tests
results = await run_rulepack_tests(MyRulePack)
print(f"Tests passed: {results['summary']['success_rate']:.1%}")
```

### 4. Run the Demo

```bash
python examples/demo.py
```

## Architecture

### RulePack Contract

Every RulePack must implement these methods:

- `validate(request)` - Core validation logic
- `get_info()` - Basic RulePack information
- `get_metadata()` - Detailed rule catalog
- `explain(request)` - Optional failure explanations
- `health_check()` - Health status

### Validation Modes

1. **Static Mode**: JSON rules only (deterministic, compliant)
2. **Hybrid Mode**: JSON + AI validation with comparison
3. **Agentic Mode**: AI-first with JSON fallback

### Client Integration

```python
from cortx_rulepack_sdk.client import RulePackClient

# Connect to a RulePack service
async with RulePackClient("http://rulepack:8080") as client:
    response = await client.validate(request)
    explanation = await client.explain(explanation_request)
```

### Registry Integration

```python
from cortx_rulepack_sdk.registry import RegistryClient, RulePackRegistration

# Register your RulePack
async with RegistryClient("http://registry:8080") as registry:
    registration = RulePackRegistration(
        domain="my_domain",
        name="MyRulePack",
        version="1.0.0",
        endpoint_url="http://my-rulepack:8080"
    )
    await registry.register(registration)
```

## Example: Financial Record Validation

See `examples/example_rulepack.py` for a complete implementation that demonstrates:

- Required field validation
- Numeric range checks  
- Date format validation
- Pattern matching
- Custom explanations
- Error handling

## Testing Framework

The SDK includes comprehensive testing utilities:

### Contract Tests

```python
from cortx_rulepack_sdk.testing import RulePackTestSuite

test_suite = RulePackTestSuite(MyRulePack)
results = await test_suite.run_all_tests()
```

### Mock Data Generation

```python
from cortx_rulepack_sdk.testing import MockRulePackData

request = MockRulePackData.validation_request(
    domain="test",
    input_data={"field": "value"},
    mode=ValidationMode.STATIC
)
```

### Performance Benchmarking

```python
from cortx_rulepack_sdk.testing import RulePackBenchmark

benchmark = RulePackBenchmark(my_rulepack)
results = await benchmark.benchmark_validation(test_data, iterations=100)
print(f"Throughput: {results['throughput_per_second']:.1f} records/sec")
```

## Deployment Patterns

### Containerized RulePack

```dockerfile
FROM python:3.11-slim

# Install RulePack SDK
COPY requirements.txt .
RUN pip install -r requirements.txt

# Copy RulePack implementation
COPY my_rulepack/ /app/my_rulepack/
WORKDIR /app

# Expose API
EXPOSE 8080
CMD ["python", "-m", "my_rulepack.server"]
```

### Kubernetes Deployment

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: my-rulepack
spec:
  replicas: 3
  selector:
    matchLabels:
      app: my-rulepack
  template:
    metadata:
      labels:
        app: my-rulepack
    spec:
      containers:
      - name: my-rulepack
        image: my-rulepack:1.0.0
        ports:
        - containerPort: 8080
        env:
        - name: RULES_PATH
          value: "/app/config/rules.json"
```

## Best Practices

### Rule Design

- Use deterministic JSON rules as primary validation
- Add AI explanations for user guidance
- Design rules to be testable and auditable
- Version your rules and track changes

### Error Handling

- Provide clear, actionable error messages
- Include expected vs actual values
- Generate appropriate severity levels
- Handle rule execution errors gracefully

### Performance

- Process records in batches when possible
- Use streaming for large datasets
- Cache frequently accessed rule metadata
- Set appropriate timeouts

### Security

- Validate all inputs
- Sanitize error messages (no PII)
- Use secure communication (HTTPS/mTLS)
- Implement proper authentication

## Configuration

RulePacks can be configured via:

1. **Constructor parameters**
2. **Environment variables**
3. **Config files**
4. **Registry settings**

Example configuration:

```python
config = {
    "rules_path": "/app/config/rules.json",
    "debug": False,
    "timeout": 300,
    "max_failures": 1000,
    "registry_url": "http://cortx-registry:8080"
}

rulepack = MyRulePack(config)
```

## Contributing

1. Follow the RulePack contract exactly
2. Add comprehensive tests
3. Document all rules and their purpose
4. Include examples and usage patterns
5. Test with multiple validation modes

## Support

For questions and support:

- Review the example implementation
- Run the demo script
- Check the test utilities
- Refer to CORTX documentation

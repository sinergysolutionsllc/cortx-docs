# CORTX Workflow Service - Functional Design Document

**Version**: 1.0.0
**Last Updated**: 2025-10-08
**Status**: Active

## 1. Purpose and Scope

### 1.1 Purpose

Orchestrates complex multi-step business workflows defined in WorkflowPacks, managing execution state, dependencies, error handling, and recovery across distributed CORTX services.

### 1.2 Scope

- WorkflowPack parsing and validation
- Step execution orchestration
- Dependency management
- Conditional logic (if/else, switch)
- Loop execution (for, while)
- Error handling and retries
- State persistence
- Workflow monitoring

### 1.3 Out of Scope

- Workflow authoring UI (handled by Designer)
- Long-running batch jobs (handled by separate batch processor)
- Real-time streaming workflows

## 2. Key Features

### 2.1 WorkflowPack Execution

- **Step Orchestration**: Execute steps in dependency order
- **Parallel Execution**: Run independent steps concurrently
- **Sequential Execution**: Run dependent steps in order
- **Conditional Branches**: if/else logic
- **Loops**: Iterate over collections or conditions

### 2.2 State Management

- **Execution Context**: Shared variables across steps
- **Step Outputs**: Pass data between steps
- **Persistence**: Save state to database
- **Recovery**: Resume from last successful step

### 2.3 Error Handling

- **Retry Logic**: Configurable retry with exponential backoff
- **Fallback Steps**: Execute alternative steps on failure
- **Error Propagation**: Bubble up or handle locally
- **Compensation**: Rollback completed steps on failure

### 2.4 Integration

- **Service Calls**: Invoke any CORTX service
- **External APIs**: Call third-party APIs
- **Webhooks**: Trigger external systems
- **Events**: Publish workflow events

## 3. API Contracts

### 3.1 Execute Workflow

```
POST /v1/workflows/execute
Body:
  {
    "workflow_pack_id": "uuid",
    "version": "1.0.0",
    "inputs": {...},
    "options": {
      "timeout_seconds": 300,
      "max_retries": 3
    }
  }
Response: 202 Accepted
  {
    "execution_id": "uuid",
    "status": "running",
    "started_at": "ISO8601"
  }
```

### 3.2 Get Execution Status

```
GET /v1/workflows/executions/{execution_id}
Response: 200 OK
  {
    "execution_id": "uuid",
    "status": "completed",
    "current_step": "step-5",
    "completed_steps": ["step-1", "step-2", ...],
    "outputs": {...},
    "duration_ms": 12500
  }
```

### 3.3 Cancel Execution

```
POST /v1/workflows/executions/{execution_id}/cancel
Response: 200 OK
  {
    "execution_id": "uuid",
    "status": "cancelled"
  }
```

## 4. Dependencies

### 4.1 Upstream

- **Validation Service**: Data validation steps
- **Compliance Service**: Compliance checks
- **Ledger Service**: Audit logging
- **AI Broker**: AI-powered steps
- **External APIs**: Third-party integrations

### 4.2 Downstream

- **Gateway**: Workflow invocation
- **Designer**: WorkflowPack deployment
- **ThinkTank**: Conversational workflows

## 5. Data Models

### 5.1 WorkflowPack

```python
@dataclass
class WorkflowPack:
    id: UUID
    name: str
    version: str
    steps: List[WorkflowStep]
    inputs: dict
    outputs: dict
    metadata: dict
```

### 5.2 WorkflowStep

```python
@dataclass
class WorkflowStep:
    id: str
    type: Literal["service_call", "condition", "loop", "parallel"]
    service: Optional[str]
    endpoint: Optional[str]
    inputs: dict
    outputs: dict
    dependencies: List[str]
    on_error: ErrorHandler
```

### 5.3 WorkflowExecution

```python
@dataclass
class WorkflowExecution:
    id: UUID
    workflow_pack_id: UUID
    status: Literal["running", "completed", "failed", "cancelled"]
    started_at: datetime
    completed_at: Optional[datetime]
    current_step: Optional[str]
    context: dict
    outputs: Optional[dict]
    error: Optional[str]
```

## 6. Configuration

| Variable | Default | Description |
|----------|---------|-------------|
| `WORKFLOW_TIMEOUT_SECONDS` | 300 | Default workflow timeout |
| `MAX_PARALLEL_STEPS` | 10 | Max concurrent steps |
| `DEFAULT_RETRY_COUNT` | 3 | Default step retries |
| `STATE_PERSISTENCE_ENABLED` | true | Persist execution state |
| `DATABASE_URL` | Required | PostgreSQL for state |

## 7. Workflow Patterns

### 7.1 Sequential Steps

```yaml
steps:
  - id: step1
    type: service_call
    service: validation
  - id: step2
    type: service_call
    service: compliance
    dependencies: [step1]
```

### 7.2 Parallel Steps

```yaml
steps:
  - id: parallel-group
    type: parallel
    steps:
      - id: validate-a
      - id: validate-b
      - id: validate-c
```

### 7.3 Conditional Logic

```yaml
steps:
  - id: check-amount
    type: condition
    condition: "inputs.amount > 10000"
    then:
      - id: manager-approval
    else:
      - id: auto-approve
```

### 7.4 Loop

```yaml
steps:
  - id: process-items
    type: loop
    collection: "inputs.items"
    steps:
      - id: validate-item
      - id: save-item
```

## 8. Error Handling

### 8.1 Retry Strategy

```yaml
on_error:
  retry:
    max_attempts: 3
    backoff: exponential
    initial_delay_ms: 1000
```

### 8.2 Fallback

```yaml
on_error:
  fallback:
    - id: send-alert
    - id: log-error
```

### 8.3 Compensation

```yaml
on_error:
  compensate:
    - id: rollback-step-1
    - id: rollback-step-2
```

## 9. Performance Characteristics

### 9.1 Latency

- Step overhead: < 50ms
- Service call latency: Varies by service
- State persistence: < 100ms

### 9.2 Throughput

- 100 concurrent executions per instance
- 1000 steps/second aggregate

### 9.3 Resource Requirements

- CPU: 1 core baseline, 4 cores under load
- Memory: 512MB baseline, 2GB under load
- Database: 100 IOPS baseline

## 10. Monitoring

### 10.1 Metrics

- Workflow execution count
- Success/failure rate
- Average execution time
- Step execution time
- Active executions
- Queue depth

### 10.2 Alerts

- Execution failures > 5%
- Execution time > timeout
- Queue depth > threshold
- Database connection issues

## 11. Change Log

| Version | Date | Changes |
|---------|------|---------|
| 1.0.0 | 2025-10-08 | Initial FDD creation |

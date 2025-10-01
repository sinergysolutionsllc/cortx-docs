```mermaid
graph TD
    subgraph CI/CD Pipeline
        A[Development] --> B{Git Push}
        B --> C[CI Server]
        C --> D{Build & Test}
        D -- Success --> E{Deploy to Staging}
        E --> F{Manual Approval}
        F -- Approved --> G{Deploy to Production}
    end
```

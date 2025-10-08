# Operations

Environments: dev → staging → prod. CI Gates: docs-ci, contracts-ci. Releases: semantic/changesets.

## DNS & Edge Management

- Cloudflare DNS managed via Terraform module at `infra/terraform/cloudflare`
- Supports zone creation/lookup, record management, and fed/corp/med/gov suite domains
- Cloudflare API token stored in Secret Manager; run `terraform plan` before promoting changes

## Runbooks

- Incident response tracking in PagerDuty with 15/60 minute SLA targets
- Observability dashboards provisioned through the Observability service (Port 8096)

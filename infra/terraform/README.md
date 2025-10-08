# Terraform Infrastructure

This directory houses infrastructure-as-code modules and environments for the Sinergy Solutions platform.  Each subdirectory encapsulates a discrete concern (e.g., DNS, networking, deployments).  Modules are designed to be composed by environment-specific workspaces or pipelines.

## Cloudflare DNS

- Path: `cloudflare/`
- Purpose: Manage Cloudflare zones and DNS records for `sinergysolutions.ai`, `fedsuite.ai`, `corpsuite.ai`, `medsuite.ai`, `govsuite.ai`, and future domains.
- Inputs: Cloudflare API token, account IDs (per domain), declarative list of DNS records.
- Output: Managed Cloudflare zones/records, enabling consistent DNS configuration across environments.

See `cloudflare/README.md` for detailed usage.

## Adding Additional Modules

1. Create a subdirectory under `infra/terraform/` (e.g., `networking/`, `gcp/`, `aws/`).
2. Include Terraform configuration (`main.tf`, `variables.tf`, `providers.tf`, etc.) and a README summarizing purpose and inputs.
3. Reference shared modules or create reusable modules under `infra/terraform/modules/` if appropriate.
4. Update this README with a short description of the new module for quick discovery.

---

**Conventions**

- Terraform version: `>= 1.5.0`
- Providers pinned via `terraform` block (see module-specific files).
- Environment/workspace state is managed outside this repo (e.g., Terraform Cloud, remote backend). Configure backends in environment-specific wrappers.

# Cloudflare DNS Terraform Module

This module manages Cloudflare zones and DNS records for Sinergy Solutions domains (`sinergysolutions.ai`, `fedsuite.ai`, `corpsuite.ai`, `medsuite.ai`, `govsuite.ai`, etc.).  It supports both creating new zones and managing records for existing zones.

## Features

- Create Cloudflare zones (optional) when `create_zone = true`.
- Look up existing zones by name and manage their records.
- Declarative record definition (A, AAAA, CNAME, TXT, etc.), including TTL and proxied settings.
- Supports multiple domains in a single invocation.

## Files

- `providers.tf` – required provider configuration (Cloudflare).
- `versions.tf` – Terraform version constraints.
- `variables.tf` – input variables (API token, domain map, default account ID).
- `main.tf` – core module logic (zone create/lookup, record management).
- `outputs.tf` – exposes managed zone IDs for downstream modules.
- `cloudflare.auto.tfvars.example` – sample configuration for common domains.

## Usage

```bash
cd infra/terraform/cloudflare
cp cloudflare.auto.tfvars.example cloudflare.auto.tfvars
# Edit cloudflare.auto.tfvars with real account IDs, zone settings, and records
terraform init
terraform plan
# terraform apply  # run when ready
```

### Required Inputs

- `cloudflare_api_token` – API token with permissions to read/manage zones and DNS records.
- `domains` – map describing each domain, e.g. `sinergysolutions_ai`, `fedsuite_ai`.

Example (see tfvars example file):

```hcl
cloudflare_api_token = "${CLOUDFLARE_API_TOKEN}"

domains = {
  sinergysolutions_ai = {
    zone        = "sinergysolutions.ai"
    account_id  = "XXXXXXXXXXXXXX"
    create_zone = false
    records = [
      {
        name    = "@"
        type    = "A"
        content = "203.0.113.10"
        proxied = true
      }
    ]
  }
}
```

### Outputs

- `zone_ids` – map of domain keys to Cloudflare zone IDs (useful for chaining to other modules).

## Authentication

Set `cloudflare_api_token` via tfvars or environment variable (`export TF_VAR_cloudflare_api_token=...`). The token should have:

- Zone: Read
- Zone: Edit
- Zone Settings: Edit (if creating zones)

## Extending

- Add SRV, MX, or other record types by modifying `domains.records` entries.
- Add additional domains by appending to `domains` map.
- If other modules require zone IDs, reference `module.cloudflare.zone_ids` after wrapping this configuration in a root module.

## Notes

- This module does **not** configure origin servers; it only manages DNS.
- State/backend configuration is intentionally omitted. Configure the backend in the calling workspace.
- When `create_zone = true`, supply `account_id` (Cloudflare account) and optional `plan` (defaults to `free`).

variable "cloudflare_api_token" {
  description = "API token with permissions to manage Cloudflare zones/records."
  type        = string
  sensitive   = true
}

variable "default_account_id" {
  description = "Default Cloudflare account ID. Used when creating zones and no per-domain account is supplied."
  type        = string
  default     = null
}

variable "domains" {
  description = <<EOT
Map of domains to manage. Keys are arbitrary identifiers (e.g., "sinergysolutions_ai").
Each domain entry supports:
  zone         (string, required)  - e.g., "sinergysolutions.ai"
  zone_id      (string, optional)  - existing zone ID (skip lookup)
  account_id   (string, optional)  - overrides default account when creating zone
  plan         (string, optional)  - Cloudflare plan (default "free")
  create_zone  (bool, optional)    - create zone if true (default false)
  records      (list, optional)    - DNS records to manage (default [])
    - name (string)
    - type (string)
    - content (string)
    - ttl (number, optional, default 300)
    - proxied (bool, optional, default true)
EOT
  type = map(object({
    zone        = string
    zone_id     = optional(string)
    account_id  = optional(string)
    plan        = optional(string)
    create_zone = optional(bool, false)
    records = optional(list(object({
      name    = string
      type    = string
      content = string
      ttl     = optional(number)
      proxied = optional(bool)
    })), [])
  }))
  default = {}
}

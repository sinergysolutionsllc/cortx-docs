locals {
  managed_zone_map = {
    for domain_key, domain in var.domains :
    domain_key => domain
  }
}

# Create zones when requested
resource "cloudflare_zone" "managed" {
  for_each = {
    for domain_key, domain in local.managed_zone_map :
    domain_key => domain
    if lookup(domain, "create_zone", false)
  }

  account_id = coalesce(lookup(each.value, "account_id", null), var.default_account_id)
  zone       = each.value.zone
  plan       = lookup(each.value, "plan", "free")
}

# Lookup existing zones when they already exist and we are not creating them
data "cloudflare_zone" "existing" {
  for_each = {
    for domain_key, domain in local.managed_zone_map :
    domain_key => domain
    if !lookup(domain, "create_zone", false) && lookup(domain, "zone_id", null) == null
  }

  name = each.value.zone
}

# Consolidated zone IDs map
data "cloudflare_api_token_permission_groups" "current" {}

locals {
  zone_ids = {
    for domain_key, domain in local.managed_zone_map :
    domain_key => coalesce(
      lookup(domain, "zone_id", null),
      try(cloudflare_zone.managed[domain_key].id, null),
      try(data.cloudflare_zone.existing[domain_key].id, null)
    )
  }

  record_entries = flatten([
    for domain_key, domain in local.managed_zone_map : [
      for idx, record in lookup(domain, "records", []) : {
        key      = "${domain_key}-${idx}-${record.name}-${record.type}"
        zone_id  = local.zone_ids[domain_key]
        name     = record.name
        type     = record.type
        content  = record.content
        ttl      = lookup(record, "ttl", 300)
        proxied  = lookup(record, "proxied", true)
      }
    ]
  ])
}

resource "cloudflare_record" "managed" {
  for_each = {
    for entry in local.record_entries :
    entry.key => entry
    if entry.zone_id != null
  }

  zone_id = each.value.zone_id
  name    = each.value.name
  type    = each.value.type
  content = each.value.content
  ttl     = each.value.ttl
  proxied = each.value.proxied
}

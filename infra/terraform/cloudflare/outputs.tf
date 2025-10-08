output "zone_ids" {
  description = "Map of domain keys to Cloudflare zone IDs."
  value = {
    for domain_key, domain in local.managed_zone_map :
    domain_key => coalesce(
      lookup(domain, "zone_id", null),
      try(cloudflare_zone.managed[domain_key].id, null),
      try(data.cloudflare_zone.existing[domain_key].id, null)
    )
  }
}

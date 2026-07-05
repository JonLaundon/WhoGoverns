# Source gaps

- **Ministers -> department mapping.** Not carried by the GOV.UK Organisations API. Confirm a machine-readable route (content API / ministers index at gov.uk/government/ministers) at the start of the build session; fallback is a small hand-built ~25-row table, each row cited. Blocks the Office/PersonRole records only.
- **Department budget (OSCAR) and staffing (Civil Service Statistics) reachability.** To test from the sandbox at build start; if bulk files are not reachable, becomes a one-off manual download by the sponsor.

# Source authority and registry v5

## Zasada

Authority zależy od typu claimu. Nie ma jednej globalnej hierarchii źródeł.

Najpierw użyj `source-authority --claim-type ...`, następnie wybierz bieżące źródło z live web/konektora. `Council Source Registry` jest mapą discovery, nie evidence.

## Typowe authority

- `law_regulation` — oficjalny tekst aktu / regulator / sąd / oficjalne guidance,
- `regulatory_guidance` — właściwy regulator/organ,
- `security_advisory` — vendor/maintainer, CISA KEV, NVD/CVE; OWASP jako guidance, nie dowód konkretnej podatności,
- `competitor_pricing` — oficjalny pricing/terms/checkout konkurenta,
- `internal_metric` — właściwy system of record,
- `official_technical_docs` — vendor docs/release notes/maintainer repo,
- `academic_evidence` — primary research/institution; systematic review jako synthesis,
- `vendor_policy` — oficjalna polityka/terms/docs vendora,
- `breaking_market` — primary company/government source lub wysokiej jakości wire,
- `doctrine` — versioned source/synthesis; nigdy current fact.

## Council Source Registry

Notion: bind `source_registry` via `~/.config/cometweb/ai-council-notion.json` (see example).

Każdy wpis registry ma być `Discovery Only = true`. Nie cytuj samego wpisu registry jako dowodu merytorycznego. Otwórz bieżące źródło i zweryfikuj wersję, datę oraz applicability.

`references/source-registry.json` jest bootstrapem offline. Runtime registry w Notion i live source mają pierwszeństwo.

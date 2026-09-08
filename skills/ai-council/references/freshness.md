# Freshness and temporal truth v5

## Cel

Każdy materialny claim zależny od czasu musi mieć jawne `as_of` i status temporalny. `Freshness` nie jest kosmetycznym score'em. Przeterminowany albo niezweryfikowany claim może być niedopuszczalny do decyzji.

## Pola temporalne

Dla materialnego current claimu zapisuj, gdy mają zastosowanie:

- `published_at` — kiedy źródło opublikowano,
- `effective_from` — od kiedy treść/reguła obowiązuje lub ma zastosowanie,
- `effective_to` — do kiedy obowiązuje,
- `last_verified_at` — kiedy Council sprawdził aktualny stan,
- `expires_at` — cache/verification expiry,
- `source_version`,
- `superseded_by`,
- `verified_for_decision`,
- `system_of_record_verified`,
- `freshness_policy`.

Nie utożsamiaj `published_at` z `effective_from`.

## Statusy

Używaj tylko:

- `CURRENT`,
- `NEAR_EXPIRY`,
- `STALE`,
- `SUPERSEDED`,
- `DRAFT`,
- `NOT_YET_EFFECTIVE`,
- `UNKNOWN`.

Materialny current claim o statusie innym niż `CURRENT` albo dopuszczalne `NEAR_EXPIRY` nie może wspierać bezwarunkowego GO/NO-GO.

## Polityki

Kernel jest źródłem TTL i wymogu live verification. Ogólna intencja:

- prawo/regulacja i regulatory guidance — weryfikuj live przy każdej materialnej decyzji,
- security advisory — weryfikuj live; stan może zmieniać się godzinowo,
- vendor policy / competitor pricing — krótki TTL,
- internal metrics — aktualny system of record,
- official technical docs — wersjonowanie + umiarkowany TTL,
- academic evidence — dłuższy TTL, ale zachowuj datę i status publikacji,
- doctrine/framework — versioned static, nie current fact.

## Freshness gate

Uruchom `freshness` przed Chairmanem, gdy decyzja zawiera materialne current claims. Wynik `REFRESH_REQUIRED` blokuje finalizację do czasu odświeżenia lub jawnego usunięcia claimu z reasoning path.

Nie obniżaj tylko confidence dla stale prawa/security/system-of-record. Jeśli claim jest binding, odśwież go albo użyj `DEFER`.

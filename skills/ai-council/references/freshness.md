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

## Kernel 5.0.1 — granice danych

`as_of` i wszystkie podane znaczniki weryfikacji wymagają czasu i strefy czasowej. Data bez czasu ani poprawny prefiks błędnej daty nie wystarczają. Jeśli podano kilka pól `last_verified_at`, `verified_at`, `observed_at`, muszą oznaczać tę samą chwilę; w przeciwnym razie wybierz właściwą obserwację, nie usuwaj konfliktu arbitralnie.

Kernel odrzuca jako niedopuszczalne przyszłą publikację/weryfikację, odwrócony przedział obowiązywania i nieprawidłową datę wygaśnięcia. `expires_at` i koniec TTL są granicami wyłącznymi: w chwili wygaśnięcia dowód nie jest już aktualny. Nieznana polityka daje `UNKNOWN`, zamiast przejścia do łagodniejszej polityki ogólnej.

Flagi mają być wartościami JSON `true`/`false`, nie tekstem. Puste wejście `freshness` daje `REFRESH_REQUIRED`. Wynik ocenia wyłącznie dostarczone wiersze (`coverage_assessed: false`); nie dowodzi pełnego pokrycia pytań ani faktycznego wykonania weryfikacji przez model.

[Zasady końcowego gate i migracja CLI](kernel-admission.md).

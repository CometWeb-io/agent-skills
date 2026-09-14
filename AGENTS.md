# CometWeb Agent Skills — wskazówki dla agentów

Przed zmianą pakietu skilla przeczytaj jego `SKILL.md`, lokalne instrukcje oraz zasady repozytorium w `README.md`. Rejestr `registry/skills.json` pozostaje źródłem metadanych; nie edytuj wygenerowanych adapterów jako polityki źródłowej.

## Ebooki, raporty i materiały praktyczne CometWeb

Przy tworzeniu lub poprawianiu tych materiałów przeczytaj i zastosuj `docs/EDITORIAL_VISUAL_STANDARD.md`.

W szczególności: potwierdzone problemy przed naprawą oznaczaj czerwienią, potwierdzone wyniki po ponownym teście zielenią. Statusy w tabelach i kartach przedstawiaj w zaokrąglonych etykietach z ikoną, tekstem i semantycznym tłem. Zachowuj neutralny stan braku danych. Używaj oryginalnego logo, Nunito Sans i spójnej ikonografii. Wydanie zmieniaj wyłącznie zgodnie z decyzją użytkownika.

Ten dokument jest instrukcją dla pracy nad materiałami. Sam jego zapis nie instaluje skilli w zewnętrznym środowisku i nie upoważnia do publikacji plików ani zmian produkcyjnych.

## Wycofany poprzednik AI Humanize — decyzja właściciela, 2026-09-12

`ai-antipattern-writing` (także pisownie `ai-anti-pattern` i `ai-anti-pattern-writing`) jest starą wersją `ai-humanize`, nie osobnym produktem ani potrzebnym aliasem kompatybilności. Nie przywracaj jego pakietu, wpisu rejestru, adaptera ani generatora podczas importu starszych ZIP-ów lub scalania otwartych PR-ów. Zachowaj `ai-humanize` jako jedyny kanoniczny skill tej rodziny. Historyczne wzmianki w changelogu mogą pozostać; nie przepisuj historii Git. Kontrola regresji: `tooling/tests/test_writer_retirement.py`.

## Jedno repo publiczne — ustalenie właściciela 2026-09-14

To repozytorium jest jedynym kanonicznym źródłem i jest publiczne. Poprzedni układ z prywatnym
kanonem i publicznym mirrorem (`MaciejZet/agent-skills`) został zwinięty; narzędzia mirrorowania
i procedura publikacji przez kopiowanie drzewa już nie obowiązują.

Ścieżki do lokalizacji prywatnych nie trafiają do repo. W commitowanych plikach są placeholdery,
realne wartości leżą obok w nieśledzonych plikach `*.local.json` / `*.local.txt`, wczytywanych jako
nakładka:

- `skills/cometweb-context/references/repos.local.txt` uzupełnia `repos.txt`
- `skills/cometweb-context/references/source-registry.local.json` nadpisuje wiązania w
  `source-registry.json`

Nie commituj tych plików i nie wpisuj realnych ścieżek do wersji śledzonych. Bramka
`tooling/public-safety-check.sh` skanuje to, co git faktycznie śledzi; plik ignorowany jest
z założenia niepublikowany i nie jest zgłaszany. Przed wydaniem uruchom też
`python3 tooling/public_safety.py --history`.

Publikacja przechodzi przez `tooling/publish_public_dry_run.py` i wymaga jawnej zgody per skill;
nie ma opcji pominięcia skanu bezpieczeństwa.

Odróżniaj lokalny wynik testów od GitHub Actions, obiekt drzewa od commita oraz commit od
aktualizacji gałęzi. Przy blokadzie narzędzia podaj dokładny stan; nie ogłaszaj powodzenia bez
ponownego odczytu zmienionej gałęzi.

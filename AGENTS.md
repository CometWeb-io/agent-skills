# CometWeb Agent Skills — wskazówki dla agentów

Przed zmianą pakietu skilla przeczytaj jego `SKILL.md`, lokalne instrukcje oraz zasady repozytorium w `README.md`. Rejestr `registry/skills.json` pozostaje źródłem metadanych; nie edytuj wygenerowanych adapterów jako polityki źródłowej.

## Ebooki, raporty i materiały praktyczne CometWeb

Przy tworzeniu lub poprawianiu tych materiałów przeczytaj i zastosuj `docs/EDITORIAL_VISUAL_STANDARD.md`.

W szczególności: potwierdzone problemy przed naprawą oznaczaj czerwienią, potwierdzone wyniki po ponownym teście zielenią. Statusy w tabelach i kartach przedstawiaj w zaokrąglonych etykietach z ikoną, tekstem i semantycznym tłem. Zachowuj neutralny stan braku danych. Używaj oryginalnego logo, Nunito Sans i spójnej ikonografii. Wydanie zmieniaj wyłącznie zgodnie z decyzją użytkownika.

Ten dokument jest instrukcją dla pracy nad materiałami. Sam jego zapis nie instaluje skilli w zewnętrznym środowisku i nie upoważnia do publikacji plików ani zmian produkcyjnych.

## Wycofany poprzednik AI Humanize — decyzja właściciela, 2026-09-12

`ai-antipattern-writing` (także pisownie `ai-anti-pattern` i `ai-anti-pattern-writing`) jest starą wersją `ai-humanize`, nie osobnym produktem ani potrzebnym aliasem kompatybilności. Nie przywracaj jego pakietu, wpisu rejestru, adaptera ani generatora podczas importu starszych ZIP-ów lub scalania otwartych PR-ów. Zachowaj `ai-humanize` jako jedyny kanoniczny skill tej rodziny. Historyczne wzmianki w changelogu mogą pozostać; nie przepisuj historii Git. Kontrola regresji: `tooling/tests/test_writer_retirement.py`.

# Prywatne repo — stan integracji i praca bez GitHub Actions

Stan z rozmowy z właścicielem: 2026-09-13.

## Co zostało zapisane w tej zmianie

Wyłącznie dokumentacja stanu integracji oraz instrukcja dla agentów. Żadne późniejsze poprawki kodu z paczki opisanej poniżej nie są wdrożone przez ten commit. Pliki workflow, ustawienia wydatków, uprawnienia, widoczność repo i publiczny mirror nie są zmieniane.

## Źródła i stan kodu

- Bazowy commit paczki: `868045d5ad486c96e45556c0aa7be628d8a1cd4a`.
- Paczka przekazana w rozmowie: `cometweb-skills-release-workflow-2026-09-13.zip`.
- SHA-256 paczki: `6319f37862bae63393c8ec35f753c0d934708e12ebde9e11ede3c5b2d9fd1431`.
- W paczce jest 137 plików pod `repo/`, a nie pełny klon repozytorium.
- `OVERLAY.json` zawiera bazę oraz hashe plików nakładki.
- Oddzielny PR #5 pozostaje draftem; odczytany head: `da1d1087cae7a0d9fd3cd745079004bb477b649c`. Jego zmian nie należy nadpisywać ani traktować jako już scalonych.

Zakres paczki: narzędzia dystrybucji/routingu/oceny wyników, poprawki AI Humanize, samodzielne pakiety Product Operator 1.2.0-rc.1 i Release Readiness 1.2.0-rc.3 oraz przekazanie ograniczeń wydania do planowania.

## Faktycznie wykonana ponowna weryfikacja

Ponownie porównano bajty 137 plików z manifestem: zgodne. Polecenie uruchomione w katalogu nakładki:

```bash
python -m pytest -q tooling/tests skills/*/tests --junitxml=local-junit.xml
```

Wynik: 1053 passed in 30.37s; bez niepowodzeń, błędów i pominięć.

- SHA-256 JUnit z tego przebiegu: `e6fb02227f70e7989495c99388ef43876c2a38c0ece2c50fcf4b14d3dba9f946`.
- SHA-256 logu: `cae882483622c9fcc912a52b3e2c0f6c3a4a2a12df849a50184a01fc9bfd1cd1`.

Raporty zostały przekazane w rozmowie; ten dokument nie przesyła ich zawartości. Testy dotyczą nakładki i dostarczonych przypadków, nie całego pierwotnego monorepo. Wywołania modeli: 0. Oceny ludzi: 0. GitHub Actions nie uruchamiano.

## Rozpoznana blokada

Sprawdzone ustawienie połączenia GitHub: app-specific Allow all actions. Nie rozszerzano uprawnień. Próba zapisu kodu przez create_tree została ponownie odrzucona przez kontrolę bezpieczeństwa OpenAI komunikatem: This tool call was blocked by OpenAI's safety checks. Please double check what you are sending.

Nie jest to komunikat o wyczerpaniu budżetu Actions ani odpowiedź GitHub 403. Szczegółowa przyczyna odmowy nie została udostępniona. Nie stosowano alternatywnego kanału zapisu, tokenów ani kodowania treści w celu obejścia odmowy. Wcześniej utworzony obiekt drzewa bez commita i referencji nie jest wdrożeniem.

## Praca w pełnym lokalnym checkoutcie

Właściciel zgłosił, że Actions są wyłączone z powodu budżetu. Zachowaj ten stan. Nie kupuj minut i nie włączaj zdalnych workflowów w ramach integracji.

1. Otwórz pełny checkout prywatnego `MaciejZet/agent-skills`; sprawdź origin, aktualny HEAD i niezacommitowane zmiany. Zachowaj pracę lokalną.
2. Sprawdź SHA-256 pobranej paczki i manifest 137 plików. Rozpakuj ją poza checkoutem.
3. Użyj dostarczonego `tooling/integration_preview.py` do przygotowania oddzielnego kandydata. Domyślne wyłączenie zmian `.github/workflows/` pozostaje aktywne. Rozwiąż konflikty jawnie, bez nadpisywania bieżącego drzewa.
4. Przejrzyj PR #5 osobno. Nie odtwarzaj wycofanego antipattern writera podczas scalania starych źródeł.
5. W pełnym kandydacie zweryfikuj rejestr, alias orkiestratora, adaptery, routing, zachowanie, protokoły, testy i kompletność paczek. Nie uznawaj wyniku samej nakładki za pełny test repo.
6. Zapisz dokładne polecenia, wynik, środowisko i hash źródeł. Błędy integracji rozwiąż przed oznaczeniem zmiany jako gotowej; brak zdalnego CI nie jest dowodem usterki kodu ani dowodem jego poprawności.
7. Zapisz zweryfikowane zmiany w prywatnej gałęzi/PR normalnym autoryzowanym procesem. Nie wykonuj force-push, nie zmieniaj widoczności i nie publikuj mirroru. Po zapisie odczytaj nowy commit i sprawdź zakres diffu.

## Kryterium zakończenia

Integracja jest zakończona dopiero, gdy wszystkie przyjęte zmiany kodu istnieją w zdalnym commicie/gałęzi i wyniki lokalnych kontroli pełnego kandydata są powiązane z tą zawartością. Ten commit dokumentacyjny nie spełnia samodzielnie tego kryterium.

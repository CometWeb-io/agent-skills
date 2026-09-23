# Lokalna walidacja bez GitHub Actions

Uruchamiaj w pełnym, zaufanym checkoutcie repozytorium. Skrypt nie włącza
Actions, nie instaluje zależności, nie aktualizuje gałęzi i nie publikuje paczek.
Testy repo są wykonywalnym kodem: ten runner nie jest sandboxem ani kontrolą
bezpieczeństwa dla nieznanych repozytoriów.

## Użycie

Najpierw sprawdź pełność checkoutu i plan poleceń, bez ich wykonania:

```bash
python3 tooling/validate_local.py --plan
```

W środowisku zsynchronizowanym przez `uv sync --group dev`:

```bash
python3 tooling/validate_local.py --output ../cometweb-validation-2026-09-13
```

Katalog wyniku musi być nowy, poza checkoutem, w istniejącym katalogu nadrzędnym.
Kolejny przebieg wymaga innej nazwy. Domyślny timeout każdego polecenia wynosi
300 sekund; `--timeout` przyjmuje liczby całkowite od 1 do 1800. Timeout dotyczy
bezpośredniego polecenia, nie jest gwarancją izolacji całego drzewa jego procesów.
Po timeoutcie lub błędzie uruchomienia dalsze kontrole nie są wykonywane.

## Zakres

Runner sprawdza składnię Pythona w pamięci, rejestr, alias orkiestratora,
strukturalną kompatybilność, wygenerowane adaptery w trybie `--check`, routing,
fixtures kontekstu, końcową kopertę CW-AIP oraz testy w `tooling/tests` i we
wszystkich istniejących katalogach `skills/*/tests`.

Nie generuje adapterów przed ich sprawdzeniem. Błąd rozjazdu trzeba rozwiązać
osobną, przejrzaną zmianą. Nie uruchamia instalatora, benchmarku modeli ani
pakowania. Katalogi skilli bez `tests/` są
wymieniane w raporcie; obecność skilla nie jest dowodem przetestowania zachowania.

Pytest używa `--import-mode=importlib`, żeby pliki o tej samej nazwie w różnych
pakietach nie kolidowały podczas importu. Runner czyści `PYTEST_ADDOPTS` i nadpisuje
konfiguracyjne `addopts`, aby odziedziczony filtr `-k` nie pomijał testów po cichu.
Pozostała konfiguracja pytest i pluginy środowiska nadal obowiązują.

## Wyniki i kody wyjścia

W katalogu wyniku są osobne logi, `junit.xml` oraz `report.json`.

- `0`: wszystkie zaplanowane kontrole zakończyły się powodzeniem, JUnit zawiera
  testy bez błędów i pominięć, a źródła nie zmieniły się podczas przebiegu.
- `1`: co najmniej jedna kontrola nie przeszła, test został pominięty, raport testów
  jest nieważny, nastąpił timeout/przerwanie albo zmieniły się źródła.
- `2`: nie można rozpocząć kontroli, np. checkout jest niepełny, występuje konflikt
  Git, ścieżka prowadzi przez symlink lub katalog wynikowy już istnieje.

`--plan` z kodem `0` oznacza wyłącznie przygotowanie planu, nie zaliczenie kontroli.
Status i lista `not_run` rozróżniają testy niewykonane od nieudanych. Suma testów
pochodzi z węzłów `testcase` w JUnit, nie z deklarowanej liczby w nagłówku XML.
Celowe xfail/skip także zatrzymują pełny wynik pozytywny; przejrzyj ich przyczynę,
nie usuwaj wymaganych kontroli, żeby uzyskać zielony wynik.

## Powiązanie wyniku ze źródłami

Raport zapisuje HEAD, stan dirty i SHA-256 śledzonych oraz nieignorowanych nowych
plików wraz z bitem wykonywalności. Pliki wymagane do rozpoczęcia kontroli muszą
być objęte tym odciskiem. Zmiana źródeł, HEAD lub indeksu widoczna w zapisie stanu
uniemożliwia pozytywny wynik. Błąd odczytu po zmianie również nie daje sukcesu.

Odcisk nie obejmuje ignorowanych lokalnych konfiguracji, całego środowiska,
pochodzenia zależności ani prawdziwości treści dowodów. Przebieg na brudnym drzewie
jest opisany jako dirty: HEAD sam w sobie nie identyfikuje wtedy testowanego kodu.

Runner nie cofa zmian wykonanych przez testy. Nie uruchamiaj równolegle edytora,
generatorów ani drugiej walidacji w tym samym checkoutcie. Logi mogą zawierać dane
prywatne; katalog wyniku ma uprawnienia 0700 i wymaga przeglądu przed udostępnieniem.

## Granice

To narzędzie wspiera lokalną kontrolę aktualnego repo. Wynik runnera nie oznacza
gotowości wydania, akceptacji hosta, poprawności wszystkich skilli ani
skuteczności modeli. Raportuj osobno testy hosta, providera i end-to-end.

# Ebook Publisher 1.0.0

Skill do przygotowywania ebooków CometWeb: od researchu po zweryfikowany plik PDF.
Punkt wejścia: `SKILL.md`. Instrukcje główne są krótkim kontraktem; szczegóły wczytuje się
z `references/` tylko na potrzebnym etapie.

## Użycie

Przykład: „Użyj ebook-publisher. Przygotuj ebook CometWeb o audycie dostępności,
wydanie 1.0. Najpierw research i walidacja, potem treść, redakcja i PDF zgodny z serią”.

Przykład zakresu ograniczonego: „Użyj ebook-publisher w trybie REDESIGN. Popraw okładkę
tego ebooka zgodnie z referencją. Zachowaj treść, źródła i wydanie 1.0. Bez zdjęć”.

Skill nie zakłada konkretnej aplikacji ani stałych ścieżek na komputerze użytkownika.
Wczytanie pliku w bieżącej rozmowie nie jest instalacją w innych środowiskach.
Etapy research/manuscript wymagają Python 3.10+. Pełny zestaw testów oraz kontrola
liczby stron na etapie release wymagają także `pypdf`. Niczego nie instaluje się automatycznie. Skład i renderowanie wymagają
narzędzia PDF dostępnego w danym środowisku — patrz `references/pdf-production.md`.

## Szybka kontrola lokalna

```bash
python -m unittest discover -s tests -v
python scripts/ebook_check.py init ../nowy-ebook
python scripts/ebook_check.py validate ../nowy-ebook/publication.json --stage research
```

Nowy szablon celowo NIE przechodzi walidacji. Trzeba go wypełnić wynikami rzeczywistej
pracy. Testy są syntetycznymi testami programu, a nie dowodem jakości gotowych ebooków.

## Co zawiera pakiet

Instrukcje procesu, profil wizualny CometWeb, tokeny i CSS do składu, szablony treści
i rejestru dowodów, walidator relacji i kontroli QA, testy regresji oraz scenariusze
oceny zachowania skilla. `integration/registry-entry.json` to kandydat wpisu do rejestru,
a NIE potwierdzenie, że wpis już znajduje się w repo lub że routing hosta jest aktywny.

## Zakres uprawnień

Tworzenie plików publikacji nie oznacza zgody na publikację publiczną, zmianę witryny,
pobieranie płatnych zasobów, włączanie GitHub Actions ani zmianę budżetu.
Nie dołączono fontów ani logo: należy korzystać z zatwierdzonych lokalnych zasobów.

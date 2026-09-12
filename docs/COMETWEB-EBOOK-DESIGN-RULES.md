# CometWeb Ebooks — zasady projektowania publikacji

Wersja zasad: 1.0 · decyzja użytkownika: 12 września 2026.
Zakres: ebooki CometWeb, raporty PDF, karty testowe i materiały warsztatowe. To reguły projektowe serii, nie wymagania techniczne narzędzia audytowego.

## 1. Referencja i tożsamość

Przed pracą wczytaj te zasady i obejrzyj aktualny tom referencyjny. Punktem odniesienia jest „CometWeb — SEO GEO AEO 2026”, wydanie 1.0, wariant Nunito Sans bez bocznych pasków. Zachowuj silną hierarchię okładki, prawdziwe logo, typografię i znaczące ikony; nie kopiuj błędów ani treści z innego tomu.

Używaj prawdziwego wektorowego logo CometWeb. Nie zastępuj go odrysowaną kometą, generowaną ilustracją ani faviconą niskiej rozdzielczości. Na ciemnej okładce znak i wordmark występują bez białej płytki, chyba że zatwierdzony wariant identyfikacji jej wymaga. Zachowuj proporcje znaku.

Typografia: Nunito Sans, z osadzonym podzbiorem w PDF. Sprawdź polskie znaki, cyfry, jednostki i faktyczne rozróżnienie grubości; nazwa „Bold” nie dowodzi pogrubienia glifów. Brak fontu rozwiąż lub ujawnij — nie deklaruj kroju, który się nie wyrenderował. Nie dołączaj osobnych plików fontów do paczki.

Brand: Night Black #18181B, Energy Mint #05F29B, Trust Green #04C27C, Depth Green #034C32, biały #FFFFFF. Jasna mięta służy jako akcent na ciemnym tle; drobny tekst na jasnym tle wymaga ciemniejszego koloru.

## 2. Przed i po

**Przed naprawą / wariant wadliwy:** czerwony podpis, ikona błędu lub naprawy, jasnoczerwone tło ramki albo czerwony element wykresu. Nie oznaczaj obu wariantów identyczną zielenią.

**Po naprawie / potwierdzone spełnienie kryterium:** zielony podpis i ikona potwierdzenia. „Wdrożono” i „naprawiono” są różnymi stanami. Sam spadek wartości lub liczby wykryć nie oznacza zaliczenia.

**Po zmianie bez rozstrzygnięcia:** neutralny lub bursztynowy kolor i jasny opis. Mediana LCP 4,0 → 3,0 s w syntetycznym przykładzie nie dowodzi dobrych terenowych CWV ani wzrostu konwersji. Kolor nie może dopowiadać takiej oceny.

Na wykresie wielu kategorii kolory stanów pozostają stałe między pomiarami: problem czerwony, zaliczenie zielone, nierozstrzygnięcie bursztynowe. Etap „przed” sygnalizuj osobnym czerwonym podpisem. Nie koloruj istniejącego problemu na zielono tylko dlatego, że należy do pomiaru „po”.

**Screenshot pozostaje dowodem:** zachowuj jego rzeczywiste kolory i treść. Dodawaj podpis i kolorową ramkę poza obrazem. Nie przemalowuj zarejestrowanego fałszywego sukcesu na czerwony komunikat. Wariant po naprawie może prawidłowo pokazywać czerwony błąd serwera: zielona ramka oznacza wtedy poprawną obsługę awarii, nie udany zapis.

## 3. Statusy w tabelach

Status ma zwartą zaokrągloną etykietę: **ikona + tekst + delikatne tło + obrys**. Etykieta obejmuje treść, nie całą szerokość wiersza. Nie zamieniaj całego wiersza na jaskrawy blok.

| Stan | Ikona | Tekst i ikona | Tło | Obrys |
| --- | --- | --- | --- | --- |
| Zaliczone / potwierdzona naprawa | check w okręgu | #065F46 | #ECFDF5 | #A7E6C9 |
| Problem / wariant wadliwy | krzyżyk w okręgu | #991B1B | #FEF2F2 | #FECACA |
| Wymaga oceny / nierozstrzygnięte | pytajnik lub ostrzeżenie | #92400E | #FFFBEB | #F3D39A |
| Zablokowane | kłódka | #6941A5 | #F5F1FA | #D7C6ED |
| Nie zbadano | przerywany okrąg | #475467 | #F2F4F7 | #D0D5DD |
| Nie dotyczy | minus w okręgu | #475467 | #F2F4F7 | #D0D5DD |
| W trakcie / informacja | zegar lub informacja | #175CD3 | #EFF6FF | #BFD7FB |

Blokada testu nie jest sama w sobie błędem strony. Hipoteza nie jest potwierdzonym problemem. Priorytet P0/P1/P2 oznaczaj oddzielnie: czerwony, bursztynowy i neutralny. Dodane stany objaśniaj w legendzie.

Nie rozdzielaj etykiety, ikony i tekstu między stronami. Dopasuj szerokość kolumny i odstępy zamiast zmniejszać font do nieczytelnego rozmiaru. Punkt wyjścia: tekst 8,5–9 pt, ikona ok. 12–14 px, promień 999 px. Oceniaj efekt w renderze PDF.

## 4. Ikony i ramki

Jedna rodzina liniowych ikon, siatka 24 × 24, podobna grubość linii i zaokrąglone zakończenia. Nie mieszaj emoji, pełnych piktogramów, ikon wielokolorowych i cienkich konturów.

Ikony umieszczaj przy kategorii rozdziału, rodzaju ramki, karcie testowej, statusie, wykresie i diagramie. „Wykonaj” — działanie; „Zachowaj” — dokument; „Odbierz, gdy” — lista kontrolna; „Granica” — informacja/ostrzeżenie. Ikona listy kontrolnej przy przyszłym kryterium nie oznacza wykonanego testu.

Ikona towarzyszy tekstowi; nie zastępuje nazwy stanu, osi, kryterium ani identyfikatora. Sprawdź rzeczywisty kolor SVG w PDF; nie zakładaj poprawnego dziedziczenia currentColor. Czarne ikony na czarnej okładce są błędem wydania.

Ramki i karty mają zaokrąglenie ok. 12–14 px, delikatny obrys i odstępy. Ich rodzaj wynika z treści: działanie, dowód, ograniczenie, przykład, ostrzeżenie. Nie oznaczaj wszystkiego zielonym sukcesem.

## 5. Okładka i wnętrze

Okładka: prawdziwe logo i nazwa CometWeb, kategoria, duży czytelny tytuł, wydanie, krótka obietnica oparta na treści i data źródeł. Miętą można wyróżnić jedną część tytułu. Dodatkowa kolumna może pokazywać rok i obszary z ikonami. Dolny pas zawiera wyłącznie zweryfikowane liczby rozdziałów, kart lub przykładów.

Bez generowanych zdjęć, przypadkowych kół i linii, bocznych ozdobnych pasków, imitowanych wyników produktu i fałszywych paneli klientów. Przestrzeń i tytuł są ważniejsze od liczby ozdób. Korekta graficzna nie zmienia samowolnie wydania 1.0 na 1.1 lub 2.0; rewizję projektu zapisuj osobno.

Wnętrze: jasne tło, ciemny tekst, zielone podtytuły, kolorowy numer rozdziału i ikona kategorii. Tabele: powtarzany nagłówek, czytelne kolumny, lekkie separatory, spokojne tło wierszy, zaokrąglone narożniki. Dane pozostają tekstem. Statusy korzystają z punktu 3.

Karta testowa zachowuje identyfikator, nazwę, obszar/dostęp, instrukcję, kryterium, dowód i granicę interpretacji. Krótkiej karty nie dziel między strony. Dłuższy materiał podziel jawnie zamiast zmniejszać font.

Unikaj nagłówków na końcu strony, diagramów oderwanych od opisu, samotnych linii i prawie pustych stron wynikających z mechanicznych podziałów. Nowy rozdział nie musi zawsze zaczynać nowej strony; istotne części i dodatki mogą ją otrzymać.

## 6. Wykresy i dowody

Każda grafika odpowiada na konkretne pytanie. Wykres ma nazwę miary, jednostkę, skalę, wartości, pochodzenie danych i ograniczenia. Nie dopisuj danych, nie zmieniaj mianowników i nie ukrywaj brakującego zakresu.

Rozróżniaj dane rzeczywiste, zachowaną demonstrację laboratoryjną i przykład syntetyczny. Zachowuj zakres i datę badań. Grafika dydaktyczna nie dowodzi skuteczności produktu.

Preferuj niewielkie wykresy w zaokrąglonych panelach, oszczędne linie pomocnicze, czytelne wartości i ikonę kategorii. Kolory wynikają ze znaczenia. Zaokrąglenie nie może przesuwać końca słupka względem skali. Nie sumuj nakładających się kategorii.

## 7. Kontrola wydania

1. Odczytaj właściwe źródło, referencję i pochodzenie logo.
2. Sprawdź rozdziały, karty, identyfikatory, liczby, źródła i zastrzeżenia.
3. Przejrzyj wszystkie porównania, statusy, priorytety i legendy. Nie zazieleniaj niewykonanych testów.
4. Wyrenderuj cały PDF. Obejrzyj każdą stronę oraz powiększenia okładki, statusów, wykresów i długich tabel.
5. Sprawdź fonty, polskie znaki, SVG, przepełnienia, kontrast, spis treści, zakładki i linki. Sprawdzenie geometrii nie zastępuje kontroli wizualnej.
6. Zachowaj tekstowe etykiety i opisy alternatywne. Samo tagowanie nie jest certyfikacją PDF/UA.
7. Sprawdź zgodność PDF/HTML/grafik, liczbę stron i paczkę bez plików fontów. Nie zmieniaj historycznych dowodów ani wyników przy korekcie graficznej.
8. Dołącz podgląd zmienionych stron i zapis rewizji zasad. Raportuj tylko faktycznie wykonane kontrole.

## 8. Dostępność wizualna

Kolor nie jest jedynym nośnikiem znaczenia. Tekst i forma ikony muszą wystarczać do rozróżnienia stanów. Praktyczny cel dla zwykłego tekstu: kontrast co najmniej 4,5:1; dla dużego tekstu co najmniej 3:1. Sprawdź też widok w skali szarości. To nie deklaracja zgodności całego PDF.

Źródła: W3C Understanding SC 1.4.1 Use of Color i SC 1.4.3 Contrast (Minimum):
- https://www.w3.org/WAI/WCAG22/Understanding/use-of-color.html
- https://www.w3.org/WAI/WCAG22/Understanding/contrast-minimum.html

## 9. Stosowanie

Wczytaj ten dokument przy tworzeniu ebooka lub poprawianiu PDF CometWeb. Źródło treści dostarcza faktów; referencyjny PDF jedynie wskazówek wizualnych. Nowa wyraźna decyzja użytkownika ma pierwszeństwo; aktualizację reguły zapisz w historii. Nie zmieniaj ogólnych zasad ai-humanize ani wygenerowanego routingu tylko po to, aby zapisać reguły jednej serii.

Historia: 2026-09-12 — pierwsze utrwalenie czerwonego „przed”, ikonowych etykiet statusów, okładki serii, funkcjonalnych ikon i kontroli renderu.

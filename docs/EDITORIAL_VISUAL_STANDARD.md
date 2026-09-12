# CometWeb — standard wizualny ebooków i materiałów praktycznych

Wersja standardu: 1.0. Ustalenie użytkownika: 2026-09-12.
Zakres: ebooki, raporty, checklisty, instrukcje, diagramy i materiały do pracy. Nie zmienia to logiki oceny produktu ani zasad żadnej wyszukiwarki.

## 1. Podstawa serii

Używaj oryginalnego znaku CometWeb i Nunito Sans. Znak pozyskuj z zatwierdzonego zasobu, bez odrysowywania, zastępowania faviconą lub wymyślania wersji. Kolory marki: night black #18181B, energy mint #05F29B, trust green #04C27C, depth green #034C32, white #FFFFFF. Sprawdź aktualny plik tokenów przy zmianie brandingu; nie zmieniaj kolorów po cichu.

Referencja kierunku: „CometWeb-SEO-GEO-AEO-2026-1.0-NunitoSans-bez-bocznych-paskow.pdf”. Wykorzystuj hierarchię okładki, oszczędną ikonografię, zaokrąglone karty i kompaktowe diagramy. Referencja nie zwalnia z kontroli kontrastu, znaczenia kolorów, czytelności i prawdziwości treści. Nie kopiuj jej błędów.

## 2. Przed naprawą / po naprawie

- Potwierdzony problem przed naprawą: czerwony akcent, czerwony tekst etykiety, jasnoczerwone tło oraz ikona błędu lub ostrzeżenia.
- Potwierdzona poprawa po ponownym teście: zielony lub miętowy akcent, ciemnozielona etykieta na jasnym tle oraz ikona potwierdzenia.
- „Przed migracją”, „stan bazowy” i „stara wersja” nie oznaczają automatycznie błędu. Neutralne porównanie pozostaw neutralne, gdy brak diagnozy problemu.
- „Po wdrożeniu” nie oznacza automatycznie naprawy. Bez testu użyj stanu niezweryfikowanego lub oczekiwania na retest.
- W wynikach mieszanych zachowaj semantykę każdej kategorii. Wiersz „przed” może mieć czerwony nagłówek, ale jego potwierdzona część nadal jest zielona, a błędna czerwona.
- Kolor nie może zastępować podpisu, liczby, jednostki ani zastrzeżenia. Spadek wskaźnika nie jest z definicji zły: zależy od znaczenia wskaźnika.

## 3. Status = zaokrąglona etykieta + ikona + tekst

W tabelach, kartach i diagramach status prezentuj jako kompaktową etykietę z pełnym zaokrągleniem. Stosuj ikonę z lewej strony, czytelny tekst i tło odpowiadające znaczeniu. Nie koloruj wyłącznie słowa i nie polegaj wyłącznie na kolorze.

| Stan | Ikona | Tło | Tekst | Obramowanie |
| --- | --- | --- | --- | --- |
| Potwierdzone / PASS | check-circle | #E8FBF2 | #034C32 | #B6E5D0 |
| Błąd / FAIL / Wstrzymaj | x-circle lub alert-triangle | #FEF2F2 | #991B1B | #F5C3C3 |
| Uwaga / częściowy problem | alert-triangle | #FFFBEB | #92400E | #F0D9A0 |
| Nie sprawdzono / brak danych | circle-question | #F1F4F3 | #4B5563 | #D6DFDC |
| Nie dotyczy | circle-minus | #F1F4F3 | #4B5563 | #D6DFDC |
| W trakcie / czeka na retest | clock | #EFF6FF | #1E40AF | #BFDBFE |

Stan naprawy, werdykt testu, priorytet i zgoda na wyjątek pozostają osobnymi polami. Akceptacja wyjątku nie zmienia błędu w PASS. Celowo zwrócone 404/410, zgodne z decyzją o usunięciu, nie stają się czerwonym błędem tylko z powodu kodu HTTP.

Etykiety nie dzielą się między wierszami. Pozostaw oddech wewnątrz: ikona, odstęp, tekst, margines. Dobierz szerokość do tekstu; nie zmniejszaj go do nieczytelnego rozmiaru, aby zmieścić zbyt wąską kolumnę. W A4 typowa wysokość wynosi 19–22 pt, tekst 8.5–9.5 pt; 8 pt tylko dla uzasadnionego kompaktowego zestawienia. Krótsza etykieta wymaga jednoznacznej legendy.

## 4. Ikony mają funkcję

Używaj jednego zestawu konturowego: wspólna siatka 24, grubość linii około 1.8, zaokrąglone końce. Preferuj wektory w PDF; nie używaj emoji jako ikon dokumentu.

Przypisania: dokument = wymaganie/dowód; lupa = sprawdzenie; klucz = naprawa; strzałki powrotu = retest; tarcza = odbiór/warunek; zegar = oczekiwanie; wykres = pomiar; baza = zapis operacji; glob = język/host; połączone węzły = mapa/routing.

Ikona wspiera tytuł, callout, krok lub znaczenie stanu. Nie dodawaj jej do każdego zdania. Nie stosuj zielonego ptaszka przy niewykonanym zadaniu. Zachowaj tekstowe etykiety i opisy alternatywne, gdzie format je obsługuje.

## 5. Okładka

Ciemne tło, oryginalne logo z czytelnym wordmarkiem, duży tytuł o wyraźnej hierarchii, jeden miętowy akcent znaczeniowy. Dodaj typ publikacji, zatwierdzony numer wydania i krótki rezultat pracy. Uporządkuj dolny pas informacji. Liczby na okładce muszą wynikać z faktycznej zawartości.

Nie dodawaj przypadkowych orbit, kół, linii ani ilustracji wypełniających pustkę. Grafika powinna wynikać z tematu. Duża typografia i rytm odstępów mogą wystarczyć. Nie zmieniaj wydania 1.0 na 1.1 lub 2.0 bez decyzji użytkownika.

## 6. Środek, tabele i diagramy

Jasne strony, ciemny tekst, wystarczające marginesy i powtarzalna hierarchia nagłówków. Karty i callouty mają delikatne tło i zaokrąglenie. Nie dodawaj bocznych pionowych pasków do każdej ramki. Duże nagłówki, proste tabele i ikony powinny ułatwiać skanowanie treści bez jej rozbijania na dziesiątki pustych bloków.

Diagram: krótki tytuł, ikona kategorii, czytelny kierunek, zwarte węzły, podpis i granica interpretacji. Strzałki nie przecinają etykiet. Dwa warianty porównania mają wspólną skalę. Wykresy nie dostają fikcyjnych danych dla ozdoby. Pokaż jednostkę, mianownik i źródło; oznacz dane ilustracyjne przy samym wykresie.

## 7. Odbiór i zapis zasady

1. Obejrzyj referencję i aktualny dokument; samo wydobycie tekstu nie jest oceną projektu.
2. Zachowaj treść, liczby, źródła i znaczenie statusów. Zmiana wizualna nie uprawnia do dopisywania wyników testów.
3. Sprawdź render wszystkich stron oraz osobno okładkę, statusy, porównania i najgęstsze tabele.
4. Zweryfikuj czytelność w docelowym rozmiarze, brak ucięć, brakujące glify, polskie znaki, kontrast, odsyłacze i spis treści. Nie deklaruj zgodności PDF/UA bez właściwej walidacji.
5. Dostarcz poprawiony plik i krótki podgląd kluczowych stron. Powiedz, co faktycznie zmieniono i sprawdzono.
6. Zachowaj tę regułę w repo i dołącz kopię do źródeł publikacji. Nie twierdź, że została globalnie zainstalowana, jeśli jedynie zapisano plik.
7. Nie rozpowszechniaj plików fontów w ZIP-ach ani załącznikach. Dokumenty mogą mieć font osadzony; zewnętrzne fonty pozostają lokalnymi zależnościami procesu składu.

Dla przeredagowania używaj ai-humanize z ochroną faktów; dla nowego lub zmienionego twierdzenia technicznego sprawdzaj właściwe źródło. Wizualny retusz nie oznacza automatycznej aktualizacji merytorycznej całej bibliografii.

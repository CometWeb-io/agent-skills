# Polish rule catalog

Curated editing patterns for Polish prose, with stable IDs so examples and review notes can refer to the same rule over time. The Polish catalog is not a translation of the English one. This bundle does not include a deterministic authorship scanner; use these entries as editorial heuristics, never as evidence that a model wrote the text.

Severity is editorial priority: `fatal` means remove unless an explicit exception applies, `high` and `medium` deserve review, and `low` is a preference. Allowances identify constructions that are ordinary language but become repetitive when overused.

Read [false-positives.md](false-positives.md) before treating any entry as absolute. Register, genre, and technical terminology can make a listed construction completely appropriate.

## Chat-assistant leakage (`collaborative_leakage`)

| id | severity | pattern name | fix |
|---|---|---|---|
| `AP-LEAK-051` | fatal | Wyciek asystenta czatowego | Wyrzuć. To należy do okna czatu, nie do publikowanego tekstu. |

## Knowledge-cutoff or model disclaimers (`cutoff_disclaimer`)

| id | severity | pattern name | fix |
|---|---|---|---|
| `AP-CUT-001` | fatal | Zastrzeżenie o granicy wiedzy modelu | Usuń metakomentarz. Podaj datowany fakt albo jasno napisz, że danych nie ma. |

## Negative parallelism (strongest single tell) (`negative_parallelism`)

| id | severity | pattern name | fix |
|---|---|---|---|
| `AP-NEG-051` | fatal | To nie X. To Y. | Skasuj zdanie z negacją. Zostaw tylko twierdzenie. |
| `AP-NEG-052` | fatal | Nie chodzi (tylko) o X, chodzi o Y | Napisz o co chodzi. Bez kontrastu. |
| `AP-NEG-053` | fatal | Nie tylko X, ale wręcz Y | Skasuj pierwszą połowę. Zostaw twierdzenie, które faktycznie stawiasz. |
| `AP-NEG-054` | fatal | Mniej X, więcej Y | Nazwij to, czego ma być więcej, i skończ zdanie. |
| `AP-NEG-055` | fatal | Zapomnij o X / Przestań X, zacznij Y | Wyrzuć rozbieg. Powiedz rekomendację wprost. |
| `AP-NEG-056` | fatal | Nie potrzebujesz X, potrzebujesz Y | Napisz raz, czego trzeba. |
| `AP-NEG-057` | fatal | Pytanie nie brzmi X, pytanie brzmi Y | Zadaj prawdziwe pytanie. Fałszywe skasuj. |
| `AP-NEG-058` | high | X jest przereklamowane / martwe, liczy się Y | Postaw tezę o tym, co rekomendujesz, i podeprzyj ją danymi. |
| `AP-NEG-059` | high | Choć X może się wydawać, Y w rzeczywistości | Skasuj ustępstwo. Zacznij od tego, co myślisz. |
| `AP-NEG-060` | low (first 2 free) | Nie tylko X, ale również Y (spójnik) | Poprawne, ale przy trzecim użyciu w tekście napisz to prościej. |

## Dead stock phrases (`dead_phrase`)

| id | severity | pattern name | fix |
|---|---|---|---|
| `AP-PHR-051` | high | W dzisiejszych czasach | Skasuj rozbieg. Zacznij od tematu. |
| `AP-PHR-052` | high (first 1 free) | Warto zauważyć / należy podkreślić | Skasuj ramkę. Jeśli to ważne, po prostu to napisz. |
| `AP-PHR-054` | high | Zagłębmy się / przyjrzyjmy się bliżej | Zrób to, nie zapowiadaj. |
| `AP-PHR-053` | medium | W celu (zamiast „aby”) | Napisz „aby”. |
| `AP-PHR-055` | medium | Na koniec dnia / idąc dalej | Wyrzuć. Zero informacji. |
| `AP-PHR-056` | medium | Co szczególnie interesujące / innymi słowy | Napisz obserwację raz i skasuj powtórzenie. |
| `AP-PHR-057` | medium | Mimo pozytywów, temat napotyka wyzwania | Nazwij konkretne ograniczenie i kogo dotyka. |

## Mechanical discourse transitions (`dead_transition`)

| id | severity | pattern name | fix |
|---|---|---|---|
| `AP-TRN-051` | high (first 1 free) | Ponadto / Dodatkowo na początku zdania | Zacznij od konkretu: liczba, nazwa, miejsce. |
| `AP-TRN-052` | high | Podsumowując / na zakończenie | Skasuj. Skończ na ostatniej realnej myśli. |
| `AP-TRN-053` | medium (first 1 free) | To rzekłszy / mając to na uwadze | Wyrzuć zawias albo wstaw prawdziwy kontrast. |

## Dead AI vocabulary (`dead_vocabulary`)

| id | severity | pattern name | fix |
|---|---|---|---|
| `AP-LEX-051` | high | Martwe słownictwo modeli | Wstaw zwykłe słowo, którego użyłbyś w rozmowie, albo skasuj przymiotnik i nazwij konkret. |
| `AP-LEX-052` | medium | Korpo-przymiotniki (mocne) | Zamień na konkretny opis: liczba, nazwa, zmierzony efekt. |
| `AP-LEX-053` | low (first 1 free) | Korpo-czasowniki | Zwykle wystarczy: użyć, wyciąć, wdrożyć, zmierzyć. Zostaw, jeśli naprawdę to znaczy. |
| `AP-LEX-054` | low (first 1 free) | Korpo-przymiotniki (kontekstowe) | Często poprawne w tekście technicznym. Sprawdź, czy niesie pomiar; jeśli nie, wywal. |

## Engagement bait (`engagement_bait`)

| id | severity | pattern name | fix |
|---|---|---|---|
| `AP-BAIT-051` | high | Niech to zapadnie / przeczytaj jeszcze raz | Skasuj. Zaufaj czytelnikowi. |

## Hype and superpower promises (`hype`)

| id | severity | pattern name | fix |
|---|---|---|---|
| `AP-HYPE-051` | high | Obietnice supermocy | Wstaw zmierzony efekt, który obronisz, albo skasuj obietnicę. |

## Meta commentary about the text itself (`meta_commentary`)

| id | severity | pattern name | fix |
|---|---|---|---|
| `AP-META-051` | high | W tej sekcji omówimy | Zrób to. Skasuj zapowiedź. |

## Trailing participle summary clauses (`participle_tail`)

| id | severity | pattern name | fix |
|---|---|---|---|
| `AP-PART-051` | high | Doklejony imiesłów podsumowujący | Skasuj wtrącenie. Jeśli analiza się liczy, daj jej osobne zdanie. |

## Generic template headings (`template_header`)

| id | severity | pattern name | fix |
|---|---|---|---|
| `AP-TMPL-001` | high (first 2 free) | Generyczny nagłówek szablonowy | Nazwij sekcję od faktycznej decyzji, ograniczenia, wyniku albo konkretu pod nagłówkiem. |

## Ornate replacements for is/has (`copula_avoidance`)

| id | severity | pattern name | fix |
|---|---|---|---|
| `AP-COP-051` | medium | Ozdobny zamiennik jest/ma | Napisz „jest” albo „ma”. |

## Synonym churn instead of reusing the name (`elegant_variation`)

| id | severity | pattern name | fix |
|---|---|---|---|
| `AP-ALIAS-051` | medium | Podmienianie nazwy synonimami | Użyj nazwy ponownie. Powtórzenie, które nie psuje sensu, jest naturalne. |

## False ranges that carry no information (`false_range`)

| id | severity | pattern name | fix |
|---|---|---|---|
| `AP-RANGE-051` | medium | Fałszywy zakres „od X do Y” | Skasuj. Nazwij dwie albo trzy rzeczy, o które faktycznie chodzi. |

## Commitment-avoiding hedges (`hedge_vacillation`)

| id | severity | pattern name | fix |
|---|---|---|---|
| `AP-HEDGE-051` | medium | Hedge bez stanowiska | Zajmij stanowisko albo napisz niepewność w pierwszej osobie („myślę”, „nie wiem jeszcze”). |

## Inflated significance (`puffery`)

| id | severity | pattern name | fix |
|---|---|---|---|
| `AP-PUF-051` | medium | Nadmuchane znaczenie | Podaj fakt. Znaczenie oceni czytelnik. |




## Formularzowe otwarcia i ramy (`formulaic_opener`)

| id | severity | pattern name | fix |
|---|---|---|---|
| `AP-OPEN-051` | high | W erze cyfrowej / W dzisiejszym świecie | Skasuj ramkę. Zacznij od konkretnego tematu. |
| `AP-OPEN-052` | high | W świecie, w którym… | Skasuj. Zacznij od tezy albo od danych. |
| `AP-OPEN-053` | high | Zagłębiając się w temat / Przyglądając się bliżej | Zrób to, nie zapowiadaj. |
| `AP-OPEN-054` | medium | W istocie / W gruncie rzeczy | Podaj twierdzenie bez bębna. |
| `AP-OPEN-055` | medium | Niezależnie od tego, czy jesteś X, czy Y | Zwróć się do jednego czytelnika albo wyrzuć menu. |
| `AP-OPEN-056` | medium | W tym artykule omówimy / przyjrzymy się | Skasuj. Zacznij omawiać. |

## Czasowniki korporacyjne i konsultingowe (`corporate_verb`)

| id | severity | pattern name | fix |
|---|---|---|---|
| `AP-VERB-051` | high | Wykorzystywać / aplikować (gdy wystarczy „użyć”) | Napisz „użyć”. |
| `AP-VERB-052` | high | Odblokować potencjał | Nazwij konkretny efekt albo możliwość. |
| `AP-VERB-053` | medium | Wspierać innowacyjność / kultywować kulturę | Powiedz, co zbudowano, zmieniono albo zmierzono. |
| `AP-VERB-054` | medium | Usprawniać / optymalizować (jako wypełniacz) | Nazwij krok, który stał się krótszy lub tańszy. |
| `AP-VERB-055` | medium | Empowerować / wzmacniać (zespoły) | Powiedz, kto może teraz zrobić coś, czego wcześniej nie mógł. |
| `AP-VERB-056` | low | Napędzać (wyniki, zmiany) jako pusty czasownik | Preferuj czasownik nazywający mechanizm. |

## Metafora krajobrazu / ekosystemu / podróży (`abstract_landscape`)

| id | severity | pattern name | fix |
|---|---|---|---|
| `AP-LAND-051` | medium | Krajobraz X / pejzaż X | Nazwij rynek, zestaw narzędzi albo ograniczenie. |
| `AP-LAND-052` | medium | Ekosystem X | Jeśli to nie prawdziwy ekosystem, wymień realne elementy. |
| `AP-LAND-053` | medium | Podróż X / ścieżka X | Opisz sekwencję decyzji albo porażek. |
| `AP-LAND-054` | low | Kluczowa / pivotalna rola | Podaj konkretny wkład. |

## Retoryczne rozbiegi i fałszywy kontrast (`rhetorical_setup`)

| id | severity | pattern name | fix |
|---|---|---|---|
| `AP-RHET-051` | high | Nie ulega wątpliwości / Oczywistym jest | Skasuj. Jeśli trzeba było powiedzieć — po prostu powiedz. |
| `AP-RHET-052` | medium | Prawda jest taka, że / Rzeczywistość jest taka | Zacznij od tezy. |
| `AP-RHET-053` | medium | Nie ma co ukrywać | Skasuj ostrzeżenie. Podaj punkt. |
| `AP-RHET-054` | low (first 1 free) | Z jednej strony… z drugiej | Raz w porządku. Lepiej bezpośrednie porównanie z liczbami. |

## Szablonowa struktura akapitów i list (`template_structure`)

| id | severity | pattern name | fix |
|---|---|---|---|
| `AP-STRUCT-051` | medium | Każda sekcja tej samej głębokości | Rozwiń 1–3 punkty fokusowe; wytnij symetryczne wypełniacze. |
| `AP-STRUCT-052` | medium | Lista trzech abstrakcyjnych rzeczowników | Zastąp jedną konkretną rzeczą, która ma znaczenie, albo czterema jeśli wszystkie są realne. |


## Puste wzmacniacze (`empty_intensifier`)

| id | severity | pattern name | fix |
|---|---|---|---|
| `AP-INT-051` | medium | Naprawdę / faktycznie / w istocie jako wypełniacz | Skasuj albo zastąp konkretną miarą. |
| `AP-INT-052` | medium | Niezwykle / ekstremalnie / niesamowicie (przed abstrakcyjnymi przymiotnikami) | Preferuj liczbę, porównanie albo skasuj. |
| `AP-INT-053` | low | Bardzo unikalny / dość unikalny | Unikalny już jest absolutny; wyrzuć przysłówek albo przeformułuj. |

## Pytanie jako otwarcie i engagement bait (`question_bait`)

| id | severity | pattern name | fix |
|---|---|---|---|
| `AP-Q-051` | high | Pytanie retoryczne jako pierwsze zdanie sekcji | Zacznij od odpowiedzi albo od tezy. |
| `AP-Q-052` | medium | „Gotowy na…?” / „Chcesz…?” jako zamknięcie | Podaj konkretną następną czynność. |
| `AP-Q-053` | medium | „A co gdybym powiedział, że…?” | Skasuj rozbieg. Podaj fakt. |

## Meta-zapowiedzi o tekście (`meta_announce`)

| id | severity | pattern name | fix |
|---|---|---|---|
| `AP-META-052` | high | „W tej sekcji omówimy…” | Omów. |
| `AP-META-053` | medium | „Jak wspomniano wcześniej / jak widzieliśmy” | Powtórz krótko punkt albo wytnij odwołanie. |
| `AP-META-054` | medium | „Ważne jest, aby zrozumieć, że” | Napisz to, co trzeba zrozumieć. |

## Symetria i fałszywa równowaga (`false_balance`)

| id | severity | pattern name | fix |
|---|---|---|---|
| `AP-BAL-051` | medium | Równa przestrzeń dla punktów drugorzędnych i głównych | Rozwiń to, co ma znaczenie; resztę skróć albo wytnij. |
| `AP-BAL-052` | medium | Szablon „zalety i wady”, gdy jedna strona jest słaba | Zacznij od czynnika rozstrzygającego. |

## Nadmierne hedgingi i podwójne hedge (`over_hedge`)

| id | severity | pattern name | fix |
|---|---|---|---|
| `AP-HEDGE-052` | medium | „Możliwe, że potencjalnie być może…” | Jeden hedge wystarczy; lepiej jasna teza + dane. |
| `AP-HEDGE-053` | medium | „Niektórzy mogliby argumentować, że…” bez wskazania kto | Nazwij stanowisko albo wyrzuć chochoła. |

## Formularzowe zamknięcia (`stock_close`)

| id | severity | pattern name | fix |
|---|---|---|---|
| `AP-CLOSE-051` | high | „Podsumowując / Na zakończenie / Reasumując” | Skończ na ostatnim realnym punkcie. |
| `AP-CLOSE-052` | medium | „Przyszłość X rysuje się w jasnych barwach” | Podaj następny mierzalny krok albo ryzyko. |
| `AP-CLOSE-053` | medium | „Czas pokaże” | Preferuj konkretną niepewność albo następny eksperyment. |

76 rules apply to pl text.

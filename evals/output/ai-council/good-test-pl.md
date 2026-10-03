# Rada — czy uruchomić płatny pilotaż Example Tracker dla agencji

- As Of: 2026-10-01T09:30:00+02:00 (Europe/Warsaw)
- Current Validity: VALID
- Freshness: dane z ankiety CURRENT (2026-09-27); cennik konkurencji CURRENT (2026-09-30)
- Watch Dependencies: 1 aktywna, 0 wyzwolonych

## Werdykt

TEST — Overall Decision Confidence 58%

- Council Mode: STANDARD
- Required Confidence: 70%, więc pełne GO jest niedopuszczalne
- Rekomendowana opcja: płatny pilotaż dla 5 agencji przez 6 tygodni
- Evidence Coverage: 61%; Critical Gap: brak danych o gotowości agencji do płacenia
- Contradiction Coverage: 100%; nierozwiązane krytyczne sprzeczności: 0
- Bramki: legal CLEAR, finance CLEAR
- Human Approval: not required

## Mapa pewności

| Wymiar | Pewność | Uwaga |
| --- | ---: | --- |
| Thesis | 65% | Agencje zgłaszają problem w ankiecie |
| Financial | 50% | Najsłabszy i wiążący: nie wiadomo, czy zapłacą |

## Dlaczego

1. [F] 14 z 22 ankietowanych agencji opisało ten sam problem z raportowaniem (ankieta z 2026-09-27).
2. [A] Agencje zapłacą za rozwiązanie, które skraca raportowanie o połowę.
3. [O] Pilotaż jest odwracalny i tani.

## Bramki

| Bramka | Status | Kontrole |
| --- | --- | --- |
| legal | CLEAR | Umowa pilotażowa ze standardowym szablonem |
| finance | CLEAR | Koszt pilotażu mieści się w budżecie |

## Co zmienia decyzję

- WD-1: mniej niż 2 z 5 agencji płaci po 6 tygodniach → NO-GO dla segmentu agencji.

## TEST

Kontrakt eksperymentu: 5 agencji, 6 tygodni, cena 50% listy. Kill criteria: mniej niż 2 agencje odnawiają lub czas raportowania nie spada o 30%. Decision rule: co najmniej 3 odnowienia i spadek czasu o 30% → GO dla segmentu.

## Pamięć

Zapisano: tak. Decision Key: `segment/agencje-pilotaz`. Snapshot: `a71c…09`. Current Validity: VALID. Siła sygnału historii: brak historii.

# Z01: Paczki stylów: wygląd, treść i sposób tłumaczenia
**Priorytet:** wysoki · **Zależy od:** —

## Subtaski

Do ustalenia w brainstormingu.

## O co chodzi

Dziś styl to jedno słowo i jeden opis wizualny w `styles.py`. Nie mówi nic o tym, jak tłumaczyć temat, jakim tonem mówić
ani jakich grafik używać, a od tego zależy, czy film uczy.

## Jak ma być

Paczka stylu opisuje cały sposób robienia filmu:
- wygląd: kolory, typografia, styl grafik i obrazów;
- treść: sposób mówienia i ton, dobrane do tematu;
- sposób tłumaczenia: np. hak, problem, wyjaśnienie, przykład, podsumowanie albo opowieść z bohaterem;
- rodzaje grafik: np. wzory i wykresy dla matematyki, mapy i osie czasu dla historii;
- głos i tempo lektora, muzykę, styl napisów;
- zasady merytoryczne: np. „zawsze podaj przykład liczbowy", „zaznacz, co jest uproszczeniem".

Ten sam system robi różne filmy dzięki różnym paczkom. Ekipa agentów (A) czyta paczkę, a biblioteka Remotion (R01) dostarcza jej wygląd.

## Skąd startujemy

`backend/app/pipeline/script/styles.py` ma 7 stylów z opisem wizualnym. Wnioski z B01 i B02 dostarczą zasad.

## Do rozstrzygnięcia

- Format paczki (plik danych, folder z zasobami) i kto ją tworzy: człowiek, agent czy oba.
- Ile paczek na start. Rekomendacja: dwie bardzo różne, żeby sprawdzić, że format niczego nie zakłada na sztywno.

## Kiedy skończone

Ten sam temat zrobiony z dwiema paczkami daje dwa wyraźnie różne filmy, w wyglądzie i w sposobie tłumaczenia.

# A02: Opłacalny agent-recenzent filmu
**Priorytet:** wysoki · **Zależy od:** —

## Subtaski

Do ustalenia w brainstormingu.

## O co chodzi

Nikt dziś nie ogląda filmu przed oddaniem. Błędy na ekranie, za wolne tempo albo moment, w którym widz traci zainteresowanie,
wychodzą dopiero u widza. Oglądanie każdej klatki modelem wizyjnym byłoby jednak bardzo drogie.

## Jak ma być

Agent-recenzent ogląda film jak widz i mówi konkretnie:
- w którym momencie uwaga widza spada i trzeba przyspieszyć albo zmienić obraz;
- gdzie coś jest źle na ekranie (nachodzący tekst, zła grafika, nieczytelne napisy) i wymaga poprawki;
- czy film realizuje cel edukacyjny i zasady paczki stylu.

Uwagi trafiają z powrotem do właściwej roli w ekipie (np. montażysty albo scenografa), a nie tylko do raportu.

## Skąd startujemy

Brak. Render daje plik wideo (`backend/app/pipeline/render/`), a kompozycja ma znane czasy scen i warstw.

## Do rozstrzygnięcia

Jak zrobić to tanio. Pomysły do rozważenia:
- najpierw tanie sprawdzenia bez modelu wizyjnego, na danych kompozycji (długość ujęć, czas bez zmiany obrazu, liczba słów na sekundę,
  hak w pierwszych sekundach);
- recenzja na etapie storyboardu, zanim powstanie drogie wideo;
- zrzuty tylko w kluczowych momentach (granice scen, pojawienie się tekstu) zamiast każdej klatki;
- tańszy model do przeglądu, mocniejszy tylko dla podejrzanych fragmentów.

Wnioski z B01 i B02 dostarczają kryteriów.

## Kiedy skończone

Recenzent wskazuje konkretne momenty z uzasadnieniem, poprawka po jego uwagach daje lepszy film, a koszt recenzji jest znany i akceptowalny.

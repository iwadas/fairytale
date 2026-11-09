# R01: Biblioteka komponentów Remotion i skill do jej budowy
**Priorytet:** wysoki · **Zależy od:** —

## Subtaski

Do ustalenia w brainstormingu.

## O co chodzi

Te same elementy wracają w wielu filmach: animowana mapa z trasą z punktu A do B, karta z wpisem z bloga albo artykułu, wykres,
oś czasu. Robienie ich za każdym razem od zera jest wolne i daje nierówną jakość.

## Jak ma być

**Research Remotion.** Wiemy, co Remotion potrafi i jak najlepiej z niego korzystać.

**Biblioteka komponentów wielokrotnego użytku.** Każdy komponent ma parametry, przykłady i dokumentację, z której korzystają agenci.
Kandydaci:
- mapa z trasą A→B;
- karta wpisu z bloga, artykułu albo cytatu;
- wykres;
- oś czasu;
- wzór matematyczny;
- porównanie obok siebie;
- licznik albo duża liczba;
- lista punktów;
- belka z podpisem;
- napisy karaoke;
- ruch kamery po obrazie.

**Skill do budowy biblioteki dla paczki stylu.** Dla dowolnej paczki (Z01) skill przygotowuje jej wersję biblioteki: bierze pod uwagę
najważniejsze komponenty i nadaje im wygląd paczki.

## Skąd startujemy

`services/render-engine/remotion-app/` ma jedną kompozycję karaoke. Jest skill `remotion-best-practices`
(`services/render-engine/remotion-app/.agents/skills/`) z regułami m.in. dla przejść, napisów, animacji tekstu i map (maplibre).

## Do rozstrzygnięcia

- Jedna biblioteka z motywem z paczki czy osobna biblioteka na paczkę. Rekomendacja: jedna wspólna biblioteka, a paczka dostarcza
  motyw i ewentualne warianty, bo poprawka komponentu działa wtedy wszędzie.
- Lista komponentów na start: wybrać po researchu B01, które elementy wracają najczęściej.

## Kiedy skończone

Pierwsze komponenty działają w filmach z dwóch różnych paczek, a skill potrafi przygotować bibliotekę dla nowej paczki bez pisania
komponentów od zera.

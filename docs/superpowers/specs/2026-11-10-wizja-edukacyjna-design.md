# Wizja: system wieloagentowy do edukacyjnych filmów wideo

**Status:** szkic kierunku (brainstorm w toku) · **Data:** 2026-11-10

To dokument kierunku, a nie specyfikacja do implementacji. Ustala, czym ma być produkt, i porządkuje epiki w `tasks/`.
Szczegółowe specyfikacje powstaną osobno dla poszczególnych podepików.

## Po co

Aplikacja ma generować krótkie filmy, które **czegoś uczą**, a nie tylko przyciągają uwagę. To jednocześnie temat pracy inżynierskiej
właściciela projektu:

> *Projekt i implementacja systemu wspomagającego generowanie edukacyjnych materiałów wideo z wykorzystaniem architektury
> wieloagentowej oraz modeli sztucznej inteligencji.*

Dlatego decyzje produktowe muszą dawać się dobrze opisać i obronić w pracy: architektura wieloagentowa, jej role
i przepływ danych mają być czytelne, a nie przypadkowe.

## Ustalenia

**Edukacja jako soczewka.** Edukacja nie jest osobnym epikiem, tylko kryterium dla wszystkich: ekipa agentów (A), paczki stylów (Z),
kompozycja (R), dźwięk (D) i interfejs (G) mają służyć temu, żeby widz zrozumiał i zapamiętał temat.

**Format filmu.** Pojedyncze, samodzielne filmy o długości od 30 sekund do 3 minut (pomiędzy krótkim shortem a dłuższym wyjaśnieniem).
Długość jest parametrem filmu. Serie lekcji i kursy nie są w zakresie na start.

**Tryby pracy.** „Wspomaganie" obejmuje też wykonanie całej pracy od początku do końca:
- **pełna generacja:** użytkownik podaje temat i paczkę stylu, system oddaje gotowy film;
- **generacja krokowa:** użytkownik zatwierdza lub poprawia kolejne etapy (scenariusz, storyboard, ujęcia, montaż), zanim system pójdzie dalej.

Dokładny kształt trybów i ewentualne warianty pośrednie są do przemyślenia (podepik A01).

**Paczki stylów zamiast jednego słowa.** Styl to pełny opis sposobu robienia filmu, nie tylko wyglądu. Paczka zawiera:
- wygląd: kolory, typografia, styl grafik i obrazów;
- treść: sposób mówienia i ton, dobrane do tematu;
- sposób tłumaczenia: np. hak, problem, wyjaśnienie, przykład, podsumowanie albo opowieść z bohaterem;
- rodzaje grafik: np. wzory i wykresy dla matematyki, mapy i osie czasu dla historii;
- głos i tempo lektora, muzykę, styl napisów;
- zasady merytoryczne: np. „zawsze podaj przykład liczbowy", „zaznacz, co jest uproszczeniem".

Dzięki paczkom system może być uniwersalny, a specjalizację dostaje przez paczkę: „pochodne w stylu spokojnego tutora" i „upadek Rzymu
w stylu storytellingu" to ten sam system z inną paczką. Paczki zastępują style zaszyte dziś w `backend/app/pipeline/script/styles.py`
(podepik Z01).

**Porównanie do pracy inżynierskiej.** Robione później i z boku, bez dużego nakładu. Punkty odniesienia: obecny pipeline (kilka promptów
w łańcuchu) i jeszcze prostsze podejście (np. jeden prompt). Docelowy system wieloagentowy ma wypaść najlepiej (podepik B03).

## Otwarte tematy

Każdy temat jest podepikiem w `to_do/` właściwego epiku, do osobnego brainstormu.

| Id | Temat |
|---|---|
| A01 | Tryby pracy: pełna i krokowa generacja |
| A02 | Opłacalny agent-recenzent filmu (klatki, uwaga widza, tempo, błędy na ekranie) |
| A03 | Agent postprodukcji (animacje, przejścia, wykończenie) |
| Z01 | Paczki stylów: wygląd, treść i sposób tłumaczenia |
| R01 | Biblioteka komponentów Remotion i skill do jej budowy dla dowolnej paczki |
| B01 | Research: co działa w krótkich filmach (TikTok, Reels, Shorts) |
| B02 | Research: jak ludzie uczą się z krótkich filmów (propozycja) |
| B03 | Porównanie z prostszymi podejściami do pracy inżynierskiej |

## Do rozstrzygnięcia

- **Dziedzina na start.** Czy system jest od razu uniwersalny, czy ma jedną dziedzinę, w której jest wyjątkowo dobry i którą pokażemy
  w pracy. Paczki stylów pozwalają odłożyć tę decyzję.
- **Kiedy film jest dobry edukacyjnie.** Co widz ma wiedzieć albo umieć po obejrzeniu. Od tego zależy praca recenzenta (A02)
  i ocena w pracy (B03).

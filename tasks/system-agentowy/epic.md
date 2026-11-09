# System agentowy
**Prefiks podepików:** A

Film tworzy zespół agentów zorganizowany jak prawdziwa ekipa filmowa, a nie pipeline, w którym prompt idzie za promptem.
Każda rola ma swój zakres odpowiedzialności. Role pracują na wspólnym materiale, oceniają nawzajem swoją pracę i poprawiają ją,
aż film jest spójny.

## Kierunek

**Ekipa z rolami.** Przykładowy skład (do doprecyzowania):
- producent: pilnuje celu, formatu, budżetu i spójności całości;
- scenarzysta: historia, struktura, hook i tekst lektora;
- reżyser: wizja, podział na sceny, rytm i decyzje wizualne;
- operator i scenograf: kadry, ruch kamery, styl, spójność postaci i miejsc;
- dźwiękowiec: głos, pauzy, muzyka i efekty;
- montażysta: timeline, cięcia, tempo i napisy;
- krytyk: ocenia wynik i odsyła do poprawki.

**Wspólny dokument produkcji.** Jedno źródło prawdy o filmie: scenariusz, lista scen i ujęć, styl, postacie, decyzje i ich powody.
Agenci czytają go i zapisują do niego, zamiast przekazywać sobie surowe prompty.

**Iteracje zamiast jednego przejścia.** Rola może odrzucić albo poprawić pracę poprzedniej, np. reżyser odsyła scenariusz.
Pętle mają limit, żeby film nie kręcił się w nieskończoność.

**Człowiek w pętli.** Twórca widzi, kto co zrobił i dlaczego. Może wejść na każdym etapie, zatwierdzić albo poprawić i puścić dalej.
Postęp widać na żywo w aplikacji.

**Spójność całego filmu.** Postacie, miejsca i styl są stałe od pierwszej do ostatniej sceny. Wraca tu temat Characters/Places,
dziś odłożony.

**Dostawcy wymienialni.** Role nie zależą od konkretnego modelu LLM, TTS ani wideo. Zmiana dostawcy to zmiana konfiguracji.

**Koszt i czas pod kontrolą.** Najpierw tani szkic (scenariusz, storyboard), dopiero potem drogie generowanie wideo.
Przed uruchomieniem widać, ile mniej więcej zajmie i będzie kosztować.

**Mierzalna jakość.** Sposób sprawdzenia, czy ekipa robi lepsze filmy niż obecny pipeline, np. ten sam temat zrobiony
oboma sposobami i oceniony według stałych kryteriów.

## Czego nie chcemy

- Więcej agentów, które są wolniejsze i droższe, a film nie jest lepszy.
- Agentów, którzy „rozmawiają", a ich praca niczego nie zmienia.
- Pełnej autonomii bez wglądu twórcy, przynajmniej na start.

## Skąd startujemy

`backend/app/pipeline/script/` generuje skrypt i rozpisuje sceny w dwóch kolejnych wywołaniach LLM (pomysły, potem rozwinięcie).
Warstwa `backend/app/ai/` obsługuje LLM, TTS i generowanie wideo. `backend/app/services/project_service.py` tworzy projekt ze skryptu.
Nie ma kolejki zadań: długie operacje działają w żądaniu HTTP albo w `BackgroundTasks`.

## Do rozstrzygnięcia

- **Na czym budować orkiestrację.** Własna, prosta warstwa albo gotowy framework (np. Claude Agent SDK, LangGraph).
  Rekomendacja: zacząć od własnej, cienkiej warstwy na istniejącym `ai/` i wybrać framework po pierwszym podepiku, gdy będzie wiadomo, czego brakuje.
- **Skład na start.** Rekomendacja: scenarzysta, reżyser i krytyk. Pozostałe role dodawać, gdy będzie widać, że coś poprawiają.
- **Kolejka zadań.** Film tworzony przez ekipę trwa długo, więc praca musi iść w tle. To wspólna potrzeba z epikiem R.

## Możliwe pierwsze kroki

Dokument produkcji jako model danych. Scenarzysta i reżyser z pętlą poprawek zamiast obecnych dwóch wywołań.
Widok pracy ekipy w aplikacji. Krytyk i porównanie jakości z obecnym pipeline.

## Podepiki

| Id | Efekt | Zależy od |
|---|---|---|
| A01 | Ten sam film można zrobić w pełni automatycznie albo krok po kroku | — |
| A02 | Recenzent wskazuje słabe momenty filmu, a koszt recenzji jest akceptowalny | — |
| A03 | Agent postprodukcji wykańcza film przejściami i animacjami | R01 |

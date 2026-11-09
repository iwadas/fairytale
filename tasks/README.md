# Tracker prac

Praca ma trzy poziomy:

| Poziom | Czym jest | Gdzie leży |
|---|---|---|
| **Epik główny** | obszar produktu, którego się nie zamyka | folder `<epik>/` z plikiem `epic.md` |
| **Podepik** | konkretny efekt, który kończymy; zwykle kilka PR-ów | folder `<Id>-opis/` w folderze statusu epiku |
| **Subtask** | spory kawałek podepiku, zwykle jeden PR | checkbox w `podepik.md` |

Epiki główne to `system-agentowy/` (A), `oprawa-graficzna/` (G) i `remotion-i-kompozycja/` (R).
Litera to prefiks id podepików, więc `A02` należy do Systemu agentowego.

```text
tasks/
  system-agentowy/
    epic.md                 opis obszaru i lista podepików
    to_do/                  podepik opisany, czeka na start
      A01-scenarzysta-jako-agent/
        podepik.md          nazwa, subtaski, opis
        plan-01-kontrakt.md szczegółowy plan subtaska, gdy ruszy praca
    in_progress/            trwają prace
    done/                   wszystkie subtaski zrobione i spełnione „Kiedy skończone"
  oprawa-graficzna/
  remotion-i-kompozycja/
```

Status wynika z folderu. Przenosimy zawsze cały folder podepiku (`git mv`) w obrębie epiku, a jednocześnie trwają najlepiej 1–3 podepiki
w całym projekcie. Wszystko, co trwa, pokazuje `ls tasks/*/in_progress`. Epiki główne nie mają statusu, a ich tabele
podają tylko efekt i zależności.

## Podepik

`podepik.md` zaczyna się od nazwy i listy subtasków, więc od razu widać, z czego składa się praca i ile jest zrobione.
Pod spodem jest opowieść o zmianie: jaki problem ma twórca filmu, jak ma wyglądać świat po zmianie i skąd startujemy.
Drobne kroki nie są subtaskami: trafiają do planu subtaska.

```markdown
# <Id>: Tytuł opisujący efekt
**Priorytet:** wysoki | średni | niski · **Zależy od:** <Id> | —

## Subtaski

- [ ] **01 Nazwa**: co powstaje. Po starcie link do planu: [plan](plan-01-nazwa.md).

## O co chodzi
Sytuacja i problem, najlepiej na przykładzie. Co tracimy, jeśli tego nie zrobimy.

## Jak ma być
Świat po zmianie, opisany obszarami, po akapicie na obszar.

## Skąd startujemy
Co już działa, czego nie ma, kluczowe pliki.

## Do rozstrzygnięcia
Otwarte decyzje człowieka, z rekomendacją. Tu także rzeczy, na które trzeba uważać.

## Kiedy skończone
Kilka sprawdzalnych zdań.
```

## Poprawka

Poprawka (`fix-<NN>-opis.md`) to wyłącznie mała usterka znaleziona po drodze: do ok. godziny pracy, kilka linijek
(co jest źle, gdzie, jak poznać, że naprawione). To pojedynczy plik w folderze statusu właściwego epiku.
Jeśli należy do trwającego podepiku, dopisz ją tam jako subtask.

## Jak przechodzi praca

Nowy pomysł omawiamy skillem `superpowers:brainstorming`, a wynik zapisujemy jako podepik w `to_do/` właściwego epiku i wiersz w jego `epic.md`.
Przy starcie cały folder idzie do `in_progress/`. Dla każdego subtaska `superpowers:writing-plans` tworzy plan w folderze podepiku,
a wykonaniem zajmuje się `superpowers:subagent-driven-development` albo `superpowers:executing-plans`.
Po ostatnim subtasku cały folder idzie do `done/`.

## Kolejność prac

Numer podepiku to stały identyfikator, a nie miejsce w kolejce. Kolejność opisuje ta lista, a tabele w `epic.md` są ułożone według niej.

Do ustalenia, gdy epiki dostaną podepiki.

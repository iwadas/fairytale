# Remotion i kompozycja
**Prefiks podepików:** R

Remotion staje się właściwym silnikiem filmów. Film składa się z warstw: wygenerowanych obrazów, wygenerowanych klipów wideo,
elementów z Remotion (napisy, typografia, grafiki, przejścia) i dźwięku. Aplikacja świadomie dobiera mieszankę tych materiałów
do konkretnego filmu.

## Kierunek

**Kontrakt zamiast kodu z AI.** Backend opisuje film w ustalonym, wersjonowanym formacie danych (sceny, warstwy, czasy, styl),
który jest sprawdzany po obu stronach. Remotion zamienia go na wideo. AI nigdy nie generuje surowego kodu kompozycji.

**Prawdziwy render z danymi projektu.** Każdy film renderuje się z własnych scen, lektora i napisów. Dziś każdy eksport dostaje
ten sam gotowy plik z przykładowymi napisami.

**Render w tle.** Render nie blokuje aplikacji, pokazuje postęp, można go ponowić albo anulować.

**Biblioteka szablonów.** Gotowe, parametryzowane elementy, np. napisy karaoke, plansze tytułowe, belki z tekstem, przejścia,
ruch kamery po statycznym obrazie, proste infografiki. Każdy nowy szablon od razu działa w każdym filmie.

**Przemyślana mieszanka materiałów.** Dla każdej sceny decydujemy, czym ją pokazać:
- obraz z ruchem: tani i szybki;
- klip wideo z AI: drogi, ale najbardziej żywy;
- czysta grafika Remotion: tekst, liczby, schematy.

Wybór zależy od typu filmu, tempa i budżetu. Zasady mają być jawne i możliwe do zmiany przez twórcę.

**Formaty.** Presety pionowy 9:16, kwadrat 1:1 i poziomy 16:9 z tego samego projektu.

**Podgląd zgodny z renderem.** Podgląd w edytorze (np. Remotion Player) pokazuje to samo, co finalny plik.

**Jeden silnik.** Po osiągnięciu tej samej jakości co obecny render usuwamy kod moviepy.

## Czego nie chcemy

- Dwóch silników renderu utrzymywanych na stałe.
- Szablonów zaszytych na sztywno w jednym filmie, których nie da się użyć ponownie.
- Mieszanki dobieranej „magicznie", bez możliwości zrozumienia i zmiany decyzji.

## Skąd startujemy

`services/render-engine/remotion-app/` ma jedną kompozycję karaoke na sztywnych danych przykładowych i backend jej nie wywołuje.
Render działa w moviepy (`backend/app/pipeline/render/`), synchronicznie, w żądaniu HTTP. `REMOTION_INTEGRATION.md` zawiera
wcześniejszy plan architektury (kontrakt, kolejka, workery, storage). Napisy karaoke z backendu mają już kształt zgodny
z danymi przykładowymi Remotion.

## Do rozstrzygnięcia

- **Zakres Remotion:** tylko nakładka napisów czy cały film. Rekomendacja: cały film, a moviepy do usunięcia.
- **Kto decyduje o mieszance:** jawne reguły czy agent (reżyser albo montażysta z epiku A). Rekomendacja: zacząć od reguł,
  a potem oddać decyzję agentowi, który te reguły zna.
- **Kolejka renderu:** po stronie Pythona czy Node. Wspólna potrzeba z epikiem A.
- **Licencja Remotion:** sprawdzić warunki licencji firmowej, jeśli produkt ma być komercyjny.

## Możliwe pierwsze kroki

Kontrakt danych i karaoke renderowane z danymi projektu. Render z backendu w tle. Pierwsze szablony. Zasady doboru mieszanki.
Podgląd w edytorze. Usunięcie moviepy.

## Podepiki

| Id | Efekt | Zależy od |
|---|---|---|
| R01 | Komponenty wielokrotnego użytku i skill budujący bibliotekę dla paczki | — |

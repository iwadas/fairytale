# Oprawa graficzna
**Prefiks podepików:** G

Aplikacja wygląda i działa jak dopracowane narzędzie do tworzenia filmów: spójnie, czytelnie i szybko. Twórca dobrze się w niej czuje
i od razu widzi, co się dzieje z jego filmem.

> Założenie do potwierdzenia: ten epik dotyczy interfejsu aplikacji. Wygląd samych filmów (napisy, typografia, przejścia)
> należy do epiku R.

## Kierunek

**Jeden spójny styl.** Wspólne kolory, typografia, odstępy i komponenty w całej aplikacji. Dziś są dwa style: ciemne szkło
w edytorze i stare jasne strony.

**Edytor jak narzędzie montażowe.** Timeline, podgląd i panele edycji są wygodne i responsywne nawet przy długim filmie.
Podgląd odpowiada temu, co wyjdzie w finalnym renderze.

**Widać pracę.** Postęp generowania, praca ekipy agentów (epik A), kolejka renderu: wszystko czytelne i na żywo, bez zgadywania,
czy coś się zawiesiło.

**Dobre stany.** Ładowanie, błędy, puste ekrany i potwierdzenia przed usunięciem zamiast `alert()` i błędów widocznych tylko w konsoli.

**Desktop jako priorytet.** Zakładam pracę na komputerze, a na telefonie najwyżej podgląd. To moje założenie do potwierdzenia.

## Czego nie chcemy

- Ładnych ekranów, które są wolniejsze albo mniej wygodne w codziennej pracy.
- Przebudowy wyglądu bez wspólnego systemu, po której po pół roku znowu są dwa style.

## Skąd startujemy

Vue 3 z vue-cli (w trybie utrzymania), Tailwind, zmienne kolorów w `frontend/src/assets/main.css` niepodpięte do Tailwinda.
Duże komponenty: `SceneEditor.vue`, `Settings.vue`, `Timeline.vue`. Warstwa API jest już w `frontend/src/api/`.
Brak zarządzania stanem (Pinia), brak TypeScriptu i testów frontendu.

## Do rozstrzygnięcia

- **Zakres:** sam interfejs aplikacji czy także wygląd filmów. Rekomendacja: interfejs tutaj, filmy w R.
- **Inspiracje:** narzędzia, których wygląd i wygodę lubisz (np. CapCut, Descript, Runway).
- **Fundament techniczny:** przejście na Vite i Pinia przed przebudową wyglądu. Rekomendacja: tak, na początku epiku, bo potem będzie drożej.

## Możliwe pierwsze kroki

Makiety kluczowych ekranów. Wspólne tokeny stylu i biblioteka podstawowych komponentów. Nowy edytor projektu. Stany i komunikaty.

## Podepiki

| Id | Efekt | Zależy od |
|---|---|---|

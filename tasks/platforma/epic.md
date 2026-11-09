# Platforma
**Prefiks podepików:** P

Fundament, na którym stoją pozostałe epiki: stabilny backend i frontend, praca w tle, narzędzia jakości kodu
i dokumentacja, dzięki której ludzie i agenci szybko odnajdują się w projekcie.

## Kierunek (do brainstormu)

- Kolejka zadań w tle dla długich operacji (generowanie, render), wspólna dla epików A i R.
- Narzędzia jakości: linter i formatter, jedno polecenie „sprawdź wszystko", CI, pre-commit.
- Dokumentacja dla agentów: `AGENTS.md`, `CLAUDE.md`, konfiguracja `.claude/`.
- Porządki w bazie: klucze obce i kaskady, migracja bazowa, która potrafi zbudować pustą bazę.
- Naprawa znanych błędów z audytu.

## Znane problemy (punkt startowy)

- Frontend: „Generate Script" zawsze rzuca błąd (literówka), w `SceneEditor.vue` są wywołania nieistniejących funkcji,
  Download zapisuje JSON jako `.mp4`, status `failed` z WebSocketa jest traktowany jak „w toku", brak ponownego łączenia WebSocketa.
- Backend: render blokuje serwer, `POST /scenes/{project_id}` przechwytuje `/scenes/add-character-to-scene`,
  brakujące zasoby dają 500 zamiast 404, osierocone rekordy po usunięciu projektu.
- Bezpieczeństwo: `GET /settings` zwraca klucze API w czystym tekście.

## Podepiki

| Id | Efekt | Zależy od |
|---|---|---|

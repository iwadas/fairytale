# System agentowy
**Prefiks podepików:** A

Film powstaje dziś w pipeline, w którym prompt idzie za promptem. Celem jest prawdziwy system agentowy zbudowany jak ekipa
filmowa: scenarzysta, reżyser, dźwiękowiec i inne role, które współpracują nad jednym filmem, zamiast wykonywać kolejne kroki
po kolei.

Skąd startujemy: `backend/app/pipeline/script/` (generowanie skryptu i rozpisywanie scen przez dwa kolejne wywołania LLM),
`backend/app/ai/` (LLM, TTS, generowanie wideo), `backend/app/services/project_service.py` (tworzenie projektu ze skryptu).

## Podepiki

Do ustalenia w brainstormingu.

| Id | Efekt | Zależy od |
|---|---|---|

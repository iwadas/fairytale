# AI Video Platform — Expert Integration TODO

# Architecture Overview

```txt
Vue Frontend
    ↓ websocket/http
FastAPI Core Backend
    ↓ queue
Redis
    ↓
Remotion Render Workers (Node.js)
    ↓
S3/R2 Storage
    ↓
CDN
```

---

# ETAP 1 — Foundation Architecture

## TODO 1 — Wydziel render engine jako osobny serwis

Stwórz osobny repo albo folder monorepo:

```txt
services/render-engine
```

Stack:
- Node.js
- TypeScript
- Remotion
- ffmpeg
- Docker

NIE mieszaj tego z FastAPI runtime.

---

## TODO 2 — Ustal contract między Python ↔ Remotion

Nigdy:
- raw JSX z AI
- raw TS codegen

Zawsze:

```json
{
  "template": "cinematic-v1",
  "fps": 30,
  "duration": 450,
  "scenes": [...]
}
```

To jest:
> Video Scene DSL

---

## TODO 3 — Zbuduj scene schema

Użyj:
- Pydantic w Pythonie
- Zod w Node

Przykład:

```json
{
  "type": "quote",
  "text": "Future belongs to builders",
  "animation": "slide-up",
  "duration": 90
}
```

Ważne:
- strict validation
- versioning
- backward compatibility

---

# ETAP 2 — Rendering Pipeline

## TODO 4 — Zbuduj render queue

Polecam:
- Redis
- BullMQ

Architektura:

```txt
FastAPI
  ↓
enqueue render job
  ↓
Redis
  ↓
Remotion worker
```

Nie renderuj synchronously.

---

## TODO 5 — Zbuduj worker orchestration

Worker lifecycle:

```txt
PICK JOB
↓
DOWNLOAD ASSETS
↓
VALIDATE PAYLOAD
↓
RENDER
↓
UPLOAD VIDEO
↓
UPDATE STATUS
↓
CLEANUP
```

Każdy krok:
- retryable
- idempotent
- logowany

---

## TODO 6 — Dodaj progress reporting

Flow:

```txt
Worker
↓
Redis pub/sub
↓
FastAPI websocket
↓
Vue progress UI
```

Statusy:
- queued
- preparing
- rendering
- encoding
- uploading
- completed
- failed

---

# ETAP 3 — Scene Engine

## TODO 7 — Zbuduj component registry

Nie dynamiczny codegen.

```ts
const registry = {
  quote: QuoteScene,
  image: ImageScene,
  splitScreen: SplitScene,
};
```

LLM wybiera:
- typ sceny
- propsy

Nigdy:
- pełny kod.

---

## TODO 8 — Zbuduj animation system

Przykład:

```ts
enterPreset: "cinematicFade"
imageMotion: "kenBurnsSlow"
textMotion: "springUp"
```

Utrzymuj własne reusable motion presets.

---

## TODO 9 — Zbuduj timeline compiler

Input:

```json
{
  "scenes": [...]
}
```

Output:

```tsx
<Sequence from={0} durationInFrames={90}>
```

LLM NIE powinien znać Remotion API.

---

# ETAP 4 — Asset Pipeline

## TODO 10 — Zbuduj centralized asset manager

Każdy asset:
- signed URL
- cache
- metadata
- duration
- dimensions

Tabela:

```txt
assets
- id
- type
- storage_url
- mime
- duration
- width
- height
```

---

## TODO 11 — Dodaj preprocessing assets

Przed renderem:
- normalize image size
- transcode audio
- validate codecs
- generate thumbnails
- waveform extraction

---

## TODO 12 — Dodaj smart caching

Hash:

```txt
hash(template + payload + assets)
```

Jeśli istnieje:
- return existing mp4.

---

# ETAP 5 — AI Layer

## TODO 13 — LLM generuje storyboard, nie kod

AI output:

```json
{
  "scene_type": "hero",
  "headline": "...",
  "emotion": "dramatic"
}
```

Nigdy JSX.

---

## TODO 14 — Dodaj AI validation layer

Pipeline:

```txt
AI Output
↓
Validation
↓
Normalization
↓
Render
```

---

## TODO 15 — Zbuduj prompt → scene planner

```txt
Prompt
↓
Script generator
↓
Scene planner
↓
Asset planner
↓
Render payload
```

---

# ETAP 6 — Production Engineering

## TODO 16 — Dockerize render workers

Musisz mieć:
- Chromium
- fonts
- ffmpeg
- codecs

w kontrolowanym środowisku.

---

## TODO 17 — Dodaj render isolation

Każdy render:
- timeout
- memory limits
- cleanup
- temp dirs

---

## TODO 18 — Monitoring

Obowiązkowo:
- render duration
- failed renders
- RAM usage
- queue depth
- asset download time
- ffmpeg failures

Polecam:
- Prometheus
- Grafana
- Sentry

---

## TODO 19 — Build render retry system

Retry:
- asset fetch fail
- transient chromium crash
- ffmpeg fail

Nie retry:
- invalid payload
- missing asset
- schema fail

---

# ETAP 7 — Advanced Features

## TODO 20 — Dynamic subtitles engine

Automatyczne:
- word highlighting
- karaoke timing
- TikTok captions

---

## TODO 21 — Audio orchestration

Dodaj:
- ducking
- fade in/out
- soundtrack layers
- voice sync

---

## TODO 22 — Motion preset system

Style:
- cinematic
- minimal
- tiktok
- apple
- documentary
- news

Każdy:
- typography
- transitions
- camera motion
- easing

---

## TODO 23 — Multi-format rendering

Support:
- 16:9
- 9:16
- 1:1
- 4:5

---

# ETAP 8 — Skalowanie

## TODO 24 — Horizontal worker scaling

Workers:
- stateless
- disposable
- autoscaled

Np:
- Kubernetes
- ECS
- Railway workers
- Fly.io machines

---

## TODO 25 — Priority queue

Obsłuż:
- free users
- pro users
- batch renders

---

## TODO 26 — Distributed rendering

Później:
- split frames
- parallel encoding
- distributed rendering

---

# ETAP 9 — UX Killer Features

## TODO 27 — Live preview renderer

Rób:
- low-res draft
- partial timeline render
- thumbnail previews

---

## TODO 28 — Real-time editor

Możliwości:
- live scene editing
- instant preview updates
- collaborative editing

---

# Najważniejsza rada architektoniczna

Nie budujesz:
> "AI generates videos"

Budujesz:
> "AI compiles structured cinematic timelines"

---

# Anti-Pattern

❌ Złe:

```txt
Prompt
↓
LLM
↓
Generated JSX
↓
Render
```

✅ Dobre:

```txt
Prompt
↓
AI Planning
↓
Scene DSL
↓
Compiler
↓
Remotion
↓
Render
```

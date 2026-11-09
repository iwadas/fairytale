# A03: Agent postprodukcji
**Priorytet:** średni · **Zależy od:** R01

## Subtaski

Do ustalenia w brainstormingu.

## O co chodzi

Surowo złożone sceny wyglądają amatorsko. Profesjonalny film ma przemyślane przejścia, animacje tekstu i grafik, akcenty zsynchronizowane
z lektorem i muzyką.

## Jak ma być

Agent postprodukcji wykańcza film: dobiera przejścia, animacje i akcenty zgodnie z paczką stylu i rytmem lektora.
Pracuje na danych kompozycji i komponentach z biblioteki Remotion (R01), a nie na pikselach.

## Skąd startujemy

Dziś przejść i animacji praktycznie nie ma, render w moviepy składa sceny na sztywno. Remotion ma gotowe mechanizmy przejść
(zob. `services/render-engine/remotion-app/.agents/skills/remotion-best-practices/rules/transitions.md`).

## Do rozstrzygnięcia

- Czy to osobna rola, czy część montażysty. Rekomendacja: zacząć jako część montażysty i wydzielić, jeśli zrobi się za duża.

## Kiedy skończone

Film z wykończeniem agenta wygląda wyraźnie lepiej niż bez niego, a wszystkie efekty pochodzą z biblioteki i paczki stylu.

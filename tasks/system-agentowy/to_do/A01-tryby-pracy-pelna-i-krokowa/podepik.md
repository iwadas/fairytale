# A01: Tryby pracy: pełna i krokowa generacja
**Priorytet:** wysoki · **Zależy od:** —

## Subtaski

Do ustalenia w brainstormingu.

## O co chodzi

„Wspomaganie" w tytule pracy nie znaczy tylko pomocy przy ręcznej pracy. Czasem twórca chce podać temat i styl i dostać gotowy film,
a czasem chce kontrolować każdy etap.

## Jak ma być

- **Pełna generacja:** użytkownik podaje temat i paczkę stylu, ekipa agentów robi cały film.
- **Generacja krokowa:** system zatrzymuje się po kolejnych etapach (scenariusz, storyboard, ujęcia, montaż), a użytkownik zatwierdza,
  poprawia albo cofa, zanim praca pójdzie dalej.

Oba tryby korzystają z tej samej ekipy agentów i tego samego dokumentu produkcji, różnią się tylko miejscami zatrzymania.

## Skąd startujemy

Dziś jest jeden przebieg: skrypt, potem sceny, bez punktów kontrolnych (`backend/app/services/project_service.py`).

## Do rozstrzygnięcia

- Czy są tryby pośrednie (np. zatrzymanie tylko po scenariuszu).
- Jakie dokładnie etapy są punktami kontrolnymi i co użytkownik może w nich zmienić.

## Kiedy skończone

Ten sam temat da się zrobić w obu trybach, a w trybie krokowym poprawka na danym etapie jest uwzględniona w dalszych etapach.

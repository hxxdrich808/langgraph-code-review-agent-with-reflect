# Code Review Agent (LangGraph + рефлексия по 4 критериям)

Агент на LangGraph, который берёт функцию на Python, пишет по ней code review,
а затем узел-критик (`reflect`) оценивает **качество самого ревью** (не кода!)
по 4 критериям: `pep8`, `type_hints`, `edge_cases`, `naming`. Если критик ставит
`needs_revision`, узел `rewrite` целенаправленно усиливает самый слабый раздел
ревью, и цикл повторяется до `max_rounds`.

## Архитектура графа

```
START → draft_review → reflect ──ok──────────────────────→ END
                           ↑ │
                           │ └─ needs_revision & round<max_rounds → rewrite ─┐
                           │                                                 │
                           └─────────────────────────────────────────────────┘
                             needs_revision & round>=max_rounds → END
```

| Узел | Роль |
|------|------|
| `draft_review` | Первичное code review по `code` (3–6 пунктов, LLM) |
| `reflect` | LLM-критик со **structured output**: баллы 0–10 по 4 критериям, `weakest_criterion`, `verdict` |
| `rewrite` | Переписывает ревью целиком, но точечно усиливая раздел, отвечающий за `weakest_criterion`; `round += 1` |

Маршрутизация после `reflect` (`route_after_reflect`):
- `verdict == "ok"` → `END`
- `verdict == "needs_revision"` и `round < max_rounds` → `rewrite` → снова `reflect`
- иначе (лимит раундов исчерпан) → `END`

## Состояние

```python
class CodeReviewState(TypedDict):
    code: str
    draft_review: str
    criteria_scores: dict[str, int]     # {"pep8": 0-10, "type_hints": ..., "edge_cases": ..., "naming": ...}
    weakest_criterion: str
    verdict: str                        # "ok" | "needs_revision"
    round: int
    max_rounds: int
```

`verdict = "ok"`, если все 4 критерия ≥ 7 (порог задаётся `OK_THRESHOLD` в `agent.py`).

## Стек

- Python 3.10+
- `langgraph` — граф с циклом рефлексии
- `langchain-openai` — LLM-провайдер
- `pydantic` — structured output критика
- `rich` — форматированный CLI-вывод (подсветка кода, панели, таблица баллов)

## Установка

```bash
pip install -r requirements.txt
cp .env.example .env
# затем впишите в .env свой OPENAI_API_KEY
```

Используется провайдер **OpenAI** (`langchain-openai`), модель по умолчанию —
`gpt-4o-mini` (переопределяется через `OPENAI_MODEL` в `.env`).

## Запуск демо

```bash
# Встроенный пример (sort_numbers)
python demo.py

# Своя функция из файла
python demo.py --file my_module.py

# Изменить лимит раундов доработки (по умолчанию 2)
python demo.py --max-rounds 3
```

Демо использует `graph.stream(state, stream_mode="updates")`, поэтому в
консоль последовательно выводится:
1. исходный код (подсветка синтаксиса через `rich.syntax.Syntax`);
2. первичный `DRAFT REVIEW` (панель `rich.panel.Panel` с рендером Markdown);
3. результат `REFLECT` — таблица `rich.table.Table` с баллами по 4 критериям
   (цвет ячейки: зелёный ≥7 / жёлтый 4–6 / красный <4), пометка `weakest_criterion`
   и цветной `verdict`;
4. если `needs_revision` — панель `REWRITE` с переписанным ревью и новым раундом,
   затем повторный `REFLECT` с обновлёнными баллами;
5. шаги 3–4 повторяются, пока `verdict != "ok"` и `round < max_rounds`;
6. финальная сводка (число раундов, итоговый вердикт, итоговые баллы, финальный текст ревью).

Вывод целиком оформлен через библиотеку [`rich`](https://github.com/Textualize/rich)
(`Console`, `Panel`, `Table`, `Syntax`, `Markdown`, `Rule`, `Text`) — см. `demo.py`.

### Пример кода из демо по умолчанию

```python
def sort_numbers(arr):
    return sorted(arr)
```

У этой функции нет type hints, нет обработки `None`/пустого списка/невалидного
типа на входе — поэтому естественно ожидать, что критик первым делом занизит
баллы по `type_hints` и/или `edge_cases`, а `rewrite` доработает именно этот раздел.

## Structured output в `reflect`

`reflect` использует `llm.with_structured_output(ReflectionResult)`, где
`ReflectionResult` — Pydantic-модель с полями `pep8`, `type_hints`, `edge_cases`,
`naming` (int, 0–10), `weakest_criterion` (Literal), `verdict` (Literal `"ok"` /
`"needs_revision"`) и `justification` (текстовое обоснование). Это гарантирует
валидный, типизированный ответ критика без ручного парсинга JSON.

## Структура проекта

```
code_review_agent/
├── agent.py          # состояние, узлы, structured output, сборка графа
├── demo.py           # CLI-демо с потоковым выводом шагов
├── requirements.txt
├── .env.example
└── README.md
```

## Ограничения

- Для реального запуска нужен доступ к OpenAI API (ключ `OPENAI_API_KEY`). 

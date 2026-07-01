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

## Установка

```bash
pip install -r requirements.txt
cp .env.example .env
# затем впишите в .env свой OPENAI_API_KEY (или переключитесь на Ollama)
```

Поддерживаются два провайдера LLM (переключаются через `LLM_PROVIDER` в `.env`):
- **OpenAI** (`langchain-openai`) — по умолчанию, модель `gpt-4o-mini`.
- **Ollama** (`langchain-ollama`) — локальные модели; для `reflect` нужна модель
  с поддержкой tool-calling / structured output (например `llama3.1`, `qwen2.5`).

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
1. исходный код;
2. первичный `DRAFT REVIEW`;
3. результат `REFLECT` — баллы по 4 критериям, `weakest_criterion`, `verdict`;
4. если `needs_revision` — блок `REWRITE` с переписанным ревью и новым раундом,
   затем повторный `REFLECT` с обновлёнными баллами;
5. шаги 3–4 повторяются, пока `verdict != "ok"` и `round < max_rounds`;
6. финальная сводка (число раундов, итоговый вердикт, итоговые баллы, финальный текст ревью).

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

- Для реального запуска нужен доступ к API выбранного провайдера (ключ OpenAI
  либо локально запущенный Ollama).
- При использовании Ollama качество и стабильность structured output зависят
  от конкретной модели — не все модели одинаково надёжно возвращают строго
  типизированный JSON через tool-calling.

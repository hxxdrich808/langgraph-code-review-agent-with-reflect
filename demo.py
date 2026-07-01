"""
CLI-демо агента code review с рефлексией.

Запуск:
    python demo.py
    python demo.py --file path/to/module.py
    python demo.py --max-rounds 3

Выводит по шагам: первичный draft, баллы критика + weakest_criterion,
а при needs_revision — переписанный раздел ревью и обновлённые баллы.
"""

from __future__ import annotations

import argparse

from agent import CodeReviewState, build_graph

DEFAULT_CODE = """def sort_numbers(arr):
    return sorted(arr)
"""


def fmt_scores(scores: dict) -> str:
    return " | ".join(f"{k}={v}" for k, v in scores.items())


def run_demo(code: str, max_rounds: int = 2) -> CodeReviewState:
    graph = build_graph()

    state: CodeReviewState = {
        "code": code,
        "draft_review": "",
        "criteria_scores": {},
        "weakest_criterion": "",
        "verdict": "",
        "round": 0,
        "max_rounds": max_rounds,
    }

    print("=" * 72)
    print("КОД ДЛЯ РЕВЬЮ")
    print("=" * 72)
    print(code)

    for update in graph.stream(state, stream_mode="updates"):
        node_name, data = next(iter(update.items()))
        state.update(data)  # состояние плоское, накопительно мержим обновления

        if node_name == "draft_review":
            print("\n" + "=" * 72)
            print("DRAFT REVIEW (первичный)")
            print("=" * 72)
            print(state["draft_review"])

        elif node_name == "reflect":
            print("\n" + "-" * 72)
            print(f"REFLECT — критик (после round={state['round']})")
            print("-" * 72)
            print(f"  scores           : {fmt_scores(state['criteria_scores'])}")
            print(f"  weakest_criterion: {state['weakest_criterion']}")
            print(f"  verdict          : {state['verdict']}")

        elif node_name == "rewrite":
            print("\n" + "=" * 72)
            print(f"REWRITE -> round {state['round']} (усиливаем: {state['weakest_criterion']})")
            print("=" * 72)
            print(state["draft_review"])

    print("\n" + "#" * 72)
    print("ФИНАЛЬНЫЙ РЕЗУЛЬТАТ")
    print("#" * 72)
    print(f"Раундов доработки : {state['round']} / {state['max_rounds']}")
    print(f"Итоговый вердикт  : {state['verdict']}")
    print(f"Итоговые баллы    : {fmt_scores(state['criteria_scores'])}")
    print("\nИтоговый текст ревью:\n")
    print(state["draft_review"])

    return state


def main() -> None:
    parser = argparse.ArgumentParser(description="Code review agent с рефлексией (LangGraph)")
    parser.add_argument("--file", type=str, default=None, help="Путь к .py файлу для ревью")
    parser.add_argument("--max-rounds", type=int, default=2, help="Максимум раундов доработки (по умолчанию 2)")
    args = parser.parse_args()

    if args.file:
        with open(args.file, "r", encoding="utf-8") as f:
            code = f.read()
    else:
        code = DEFAULT_CODE

    run_demo(code, max_rounds=args.max_rounds)


if __name__ == "__main__":
    main()

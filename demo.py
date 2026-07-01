"""
CLI-демо агента code review с рефлексией. Вывод оформлен через `rich`
(подсветка кода, панели, таблица баллов критика с цветовой индикацией).

Запуск:
    python demo.py
    python demo.py --file path/to/module.py
    python demo.py --max-rounds 3
"""

from __future__ import annotations

import argparse

from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel
from rich.rule import Rule
from rich.syntax import Syntax
from rich.table import Table
from rich.text import Text

from agent import CodeReviewState, build_graph

console = Console()

DEFAULT_CODE = """def sort_numbers(arr):
    return sorted(arr)
"""

CRITERION_LABELS = {
    "pep8": "PEP8",
    "type_hints": "Type hints",
    "edge_cases": "Edge cases",
    "naming": "Naming",
}


def score_style(value: int) -> str:
    if value >= 7:
        return "bold green"
    if value >= 4:
        return "bold yellow"
    return "bold red"


def verdict_text(verdict: str) -> Text:
    if verdict == "ok":
        return Text("✅ OK", style="bold green")
    return Text("♻️  NEEDS REVISION", style="bold red")


def render_code(code: str) -> None:
    console.print(Rule("[bold cyan]КОД ДЛЯ РЕВЬЮ", style="cyan"))
    console.print(Syntax(code.strip("\n"), "python", theme="monokai", line_numbers=True))


def render_review_panel(text: str, title: str, style: str) -> None:
    console.print(Panel(Markdown(text), title=title, border_style=style, padding=(1, 2)))


def render_reflect(scores: dict, weakest: str, verdict: str, round_num: int) -> None:
    table = Table(title=f"REFLECT — критик (после round={round_num})", show_lines=True)
    table.add_column("Критерий", style="bold")
    table.add_column("Балл", justify="center")
    table.add_column("Статус", justify="center")

    for key, label in CRITERION_LABELS.items():
        value = scores.get(key, 0)
        mark = "⬅ слабейший" if key == weakest else ""
        row_style = "on grey19" if key == weakest else None
        table.add_row(
            label,
            Text(str(value), style=score_style(value)),
            mark,
            style=row_style,
        )

    console.print(table)
    console.print(Text.assemble(("Вердикт: ", "bold"), verdict_text(verdict)))


def fmt_scores_plain(scores: dict) -> str:
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

    console.print(
        Panel(
            "[bold]Code Review Agent[/bold] — LangGraph + рефлексия по 4 критериям\n"
            f"max_rounds = {max_rounds}",
            border_style="magenta",
        )
    )
    render_code(code)

    for update in graph.stream(state, stream_mode="updates"):
        node_name, data = next(iter(update.items()))
        state.update(data)  # состояние плоское, накопительно мержим обновления

        if node_name == "draft_review":
            console.print(Rule("[bold cyan]DRAFT REVIEW (первичный)", style="cyan"))
            render_review_panel(state["draft_review"], "draft_review", "cyan")

        elif node_name == "reflect":
            console.print(Rule(style="dim"))
            render_reflect(
                state["criteria_scores"],
                state["weakest_criterion"],
                state["verdict"],
                state["round"],
            )

        elif node_name == "rewrite":
            console.print(
                Rule(
                    f"[bold yellow]REWRITE → round {state['round']} "
                    f"(усиливаем: {CRITERION_LABELS[state['weakest_criterion']]})",
                    style="yellow",
                )
            )
            render_review_panel(state["draft_review"], f"rewrite (round {state['round']})", "yellow")

    console.print(Rule("[bold green]ФИНАЛЬНЫЙ РЕЗУЛЬТАТ", style="green"))
    summary = Table.grid(padding=(0, 2))
    summary.add_column(style="bold")
    summary.add_column()
    summary.add_row("Раундов доработки:", f"{state['round']} / {state['max_rounds']}")
    summary.add_row("Итоговый вердикт:", verdict_text(state["verdict"]))
    summary.add_row("Итоговые баллы:", fmt_scores_plain(state["criteria_scores"]))
    console.print(summary)
    render_review_panel(state["draft_review"], "Итоговый текст ревью", "green")

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

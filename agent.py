"""
LangGraph-агент: code review с рефлексией по 4 критериям.

Граф:

    START -> draft_review -> reflect --ok--> END
                                 ^  |
                                 |  needs_revision & round < max_rounds
                                 |  v
                              rewrite

reflect маршрутизирует:
  - verdict == "ok"                       -> END
  - needs_revision & round < max_rounds   -> rewrite -> reflect (снова)
  - needs_revision & round >= max_rounds  -> END (лимит раундов исчерпан)

Важно: объект ревью здесь — КОД. Рефлексия (критик) оценивает не общее
впечатление, а качество текста ревью по 4 конкретным критериям:
pep8, type_hints, edge_cases, naming.
"""

from __future__ import annotations

import os
from typing import Literal, TypedDict

from dotenv import load_dotenv
from langchain_core.prompts import ChatPromptTemplate
from langgraph.graph import END, StateGraph
from pydantic import BaseModel, Field

load_dotenv()

CRITERIA = ["pep8", "type_hints", "edge_cases", "naming"]
OK_THRESHOLD = 7  # балл, начиная с которого критерий считается закрытым


# ---------------------------------------------------------------------------
# LLM factory — поддерживает OpenAI и Ollama через одну и ту же интерфейсную
# точку. Провайдер выбирается переменной окружения LLM_PROVIDER.
# ---------------------------------------------------------------------------

def get_llm(temperature: float = 0.3):
    provider = os.getenv("LLM_PROVIDER", "openai").lower()

    if provider == "ollama":
        from langchain_ollama import ChatOllama

        model = os.getenv("OLLAMA_MODEL", "llama3.1")
        return ChatOllama(model=model, temperature=temperature)

    from langchain_openai import ChatOpenAI

    model = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
    return ChatOpenAI(model=model, temperature=temperature)


# ---------------------------------------------------------------------------
# Состояние графа
# ---------------------------------------------------------------------------

class CodeReviewState(TypedDict):
    code: str
    draft_review: str
    criteria_scores: dict[str, int]  # {"pep8": 0-10, "type_hints": ..., ...}
    weakest_criterion: str
    verdict: str  # "ok" | "needs_revision"
    round: int
    max_rounds: int


# ---------------------------------------------------------------------------
# Структурированный вывод критика (structured output)
# ---------------------------------------------------------------------------

class ReflectionResult(BaseModel):
    pep8: int = Field(ge=0, le=10, description="Насколько ревью анализирует стиль/PEP8 кода (0-10)")
    type_hints: int = Field(ge=0, le=10, description="Насколько ревью анализирует типизацию кода (0-10)")
    edge_cases: int = Field(ge=0, le=10, description="Насколько ревью выявляет граничные случаи и потенциальные баги (0-10)")
    naming: int = Field(ge=0, le=10, description="Насколько ревью оценивает качество именования в коде (0-10)")
    weakest_criterion: Literal["pep8", "type_hints", "edge_cases", "naming"] = Field(
        description="Критерий с наименьшим баллом (самое слабое место ревью)"
    )
    verdict: Literal["ok", "needs_revision"] = Field(
        description=f"'ok', если ВСЕ 4 критерия >= {OK_THRESHOLD}, иначе 'needs_revision'"
    )
    justification: str = Field(description="Краткое (2-3 предложения) обоснование оценок")


# ---------------------------------------------------------------------------
# Узел 1: draft_review — первичное ревью кода
# ---------------------------------------------------------------------------

DRAFT_PROMPT = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            "Ты опытный Python code reviewer. Дай code review переданного кода.\n"
            "Формат ответа: маркированный список из 3-6 пунктов, без преамбулы.\n"
            "В ревью обязательно затронь все четыре аспекта:\n"
            "1) стиль и соответствие PEP8;\n"
            "2) наличие и корректность type hints;\n"
            "3) обработку edge cases и потенциальные баги;\n"
            "4) качество именования переменных/функций.\n"
            "Указывай, что сделано хорошо, а что стоит улучшить. Пиши на русском, конкретно.",
        ),
        ("human", "Код для ревью:\n```python\n{code}\n```"),
    ]
)


def draft_review_node(state: CodeReviewState) -> dict:
    llm = get_llm(temperature=0.3)
    chain = DRAFT_PROMPT | llm
    result = chain.invoke({"code": state["code"]})
    return {
        "draft_review": result.content,
        "round": 0,
    }


# ---------------------------------------------------------------------------
# Узел 2: reflect — критик, оценивает КАЧЕСТВО ревью по 4 критериям
# ---------------------------------------------------------------------------

REFLECT_PROMPT = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            "Ты — строгий критик code review. Тебе даны исходный код и текст ревью, "
            "написанный другим ревьюером. Оцени КАЧЕСТВО ЭТОГО РЕВЬЮ (а не сам код) "
            "по 4 критериям, шкала 0-10 для каждого:\n"
            "- pep8: насколько ревью замечает и разбирает вопросы стиля/PEP8;\n"
            "- type_hints: насколько ревью оценивает наличие и корректность типизации;\n"
            "- edge_cases: насколько ревью выявляет пропущенные граничные случаи и баги;\n"
            "- naming: насколько ревью оценивает качество именования сущностей.\n\n"
            f"verdict = 'ok', если ВСЕ 4 критерия >= {OK_THRESHOLD}, иначе 'needs_revision'.\n"
            "weakest_criterion — критерий с наименьшим баллом (при равенстве нескольких "
            "минимальных баллов выбери тот, что важнее для качества ревью в данном случае).",
        ),
        (
            "human",
            "Исходный код:\n```python\n{code}\n```\n\n"
            "Текст ревью для оценки:\n{draft_review}",
        ),
    ]
)


def reflect_node(state: CodeReviewState) -> dict:
    llm = get_llm(temperature=0.0)
    structured_llm = llm.with_structured_output(ReflectionResult)
    chain = REFLECT_PROMPT | structured_llm
    result: ReflectionResult = chain.invoke(
        {"code": state["code"], "draft_review": state["draft_review"]}
    )

    scores = {
        "pep8": result.pep8,
        "type_hints": result.type_hints,
        "edge_cases": result.edge_cases,
        "naming": result.naming,
    }

    return {
        "criteria_scores": scores,
        "weakest_criterion": result.weakest_criterion,
        "verdict": result.verdict,
    }


# ---------------------------------------------------------------------------
# Узел 3: rewrite — целенаправленно усиливает самое слабое место ревью
# ---------------------------------------------------------------------------

REWRITE_PROMPT = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            "Ты дорабатываешь текст code review. Тебе даны исходный код, текущий текст "
            "ревью и критерий, который критик оценил ниже всего: {weakest_criterion}.\n"
            "Перепиши весь текст ревью заново (3-6 пунктов, тот же формат), сохранив всё "
            "ценное из прежней версии, но СУЩЕСТВЕННО усиль раздел, относящийся к "
            "критерию '{weakest_criterion}': добавь конкретику, ссылки на конкретные "
            "строки/имена из кода и предметные рекомендации. Остальные пункты не сокращай.\n"
            "Пиши на русском.",
        ),
        (
            "human",
            "Код:\n```python\n{code}\n```\n\n"
            "Текущее ревью:\n{draft_review}\n\n"
            "Критерий для усиления: {weakest_criterion}",
        ),
    ]
)


def rewrite_node(state: CodeReviewState) -> dict:
    llm = get_llm(temperature=0.3)
    chain = REWRITE_PROMPT | llm
    result = chain.invoke(
        {
            "code": state["code"],
            "draft_review": state["draft_review"],
            "weakest_criterion": state["weakest_criterion"],
        }
    )
    return {
        "draft_review": result.content,
        "round": state["round"] + 1,
    }


# ---------------------------------------------------------------------------
# Маршрутизация после reflect
# ---------------------------------------------------------------------------

def route_after_reflect(state: CodeReviewState) -> str:
    if state["verdict"] == "ok":
        return "end"
    if state["round"] < state["max_rounds"]:
        return "rewrite"
    return "end"


# ---------------------------------------------------------------------------
# Сборка графа
# ---------------------------------------------------------------------------

def build_graph():
    graph = StateGraph(CodeReviewState)

    graph.add_node("draft_review", draft_review_node)
    graph.add_node("reflect", reflect_node)
    graph.add_node("rewrite", rewrite_node)

    graph.set_entry_point("draft_review")
    graph.add_edge("draft_review", "reflect")
    graph.add_conditional_edges(
        "reflect",
        route_after_reflect,
        {"rewrite": "rewrite", "end": END},
    )
    graph.add_edge("rewrite", "reflect")

    return graph.compile()

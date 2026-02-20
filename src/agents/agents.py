from pydantic_ai import Agent

from config import settings
from agents.models import (
    AnalysisResult,
    ClassificationResult,
    SQLQuery,
)
from agents.utils import clean_prompt, get_model


def create_classification_agent(
    model_name: str = settings.DEFAULT_MODEL,
) -> Agent[None, ClassificationResult]:
    prompt = clean_prompt(settings.CLASSIFIER_PROMPT, settings.PLACEHOLDER_USER_INPUT)
    return Agent(
        model=get_model(model_name),
        system_prompt=prompt,
        result_type=ClassificationResult,
    )


def create_sql_query_agent(
    model_name: str = settings.DEFAULT_MODEL,
) -> Agent[None, SQLQuery]:
    prompt = clean_prompt(
        settings.CUSTOM_RETRIEVER_PROMPT, settings.PLACEHOLDER_USER_INPUT
    )

    return Agent(
        model=get_model(model_name),
        system_prompt=prompt,
        result_type=SQLQuery,
    )


def create_analysis_agent(
    model_name: str = settings.DEFAULT_MODEL,
) -> Agent[None, AnalysisResult]:
    prompt = clean_prompt(
        settings.ANALYZING_PROMPT, settings.PLACEHOLDER_DREAMS_THOUGHTS
    )

    return Agent(
        model=get_model(model_name),
        system_prompt=prompt,
        result_type=AnalysisResult,
    )


def create_summarization_agent(model_name: str = settings.DEFAULT_MODEL) -> Agent:
    prompt = clean_prompt(
        settings.SUMMARIZATION_PROMPT, settings.PLACEHOLDER_DREAMS_CONTENT
    )

    return Agent(
        model=get_model(model_name),
        system_prompt=prompt,
    )
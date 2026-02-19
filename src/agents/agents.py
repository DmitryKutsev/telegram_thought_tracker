from pydantic_ai import Agent
from pydantic_ai.models.openai import OpenAIModel

from config import settings
from agents.models import (
    AnalysisResult,
    ClassificationResult,
    SQLQuery,
)


def clean_prompt(prompt: str, placeholder: str) -> str:
    if placeholder in prompt:
        return prompt.split(placeholder)[0].strip()
    return prompt.strip()


def get_model(model_name: str = settings.DEFAULT_MODEL):
    if model_name in settings.TOGETHER_MODELS_LIST:
        return OpenAIModel(
            model_name,
            base_url="https://api.together.xyz/v1",
            api_key=settings.TOGETHER_API_KEY,
        )

    if model_name in settings.OPENAI_MODELS_LIST:
        return OpenAIModel(
            model_name,
            api_key=settings.OPENAI_API_KEY,
        )

    return OpenAIModel(
        model_name,
        api_key=settings.OPENAI_API_KEY,
    )


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
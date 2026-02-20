from langchain_text_splitters import RecursiveCharacterTextSplitter
from pydantic_ai.models.openai import OpenAIModel

from config import settings


def chunk_text(
    text: str,
    chunk_size_tokens: int | None = None,
    model_name: str = settings.DEFAULT_MODEL,
) -> list[str]:
    if chunk_size_tokens is None:
        chunk_size_tokens = settings.CHUNK_SIZE_TOKENS

    text_splitter = RecursiveCharacterTextSplitter.from_tiktoken_encoder(
        model_name=model_name,
        chunk_size=chunk_size_tokens,
        chunk_overlap=200,
    )

    return text_splitter.split_text(text)


def clean_prompt(prompt: str, placeholder: str) -> str:
    if placeholder in prompt:
        return prompt.split(placeholder)[0].strip()
    return prompt.strip()


def get_model(model_name: str = settings.DEFAULT_MODEL) -> OpenAIModel:
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
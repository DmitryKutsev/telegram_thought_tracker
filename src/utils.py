from langchain_text_splitters import RecursiveCharacterTextSplitter

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
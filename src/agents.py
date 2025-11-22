"""AI agents using Pydantic AI framework."""

import datetime
import os

from langchain_text_splitters import RecursiveCharacterTextSplitter
from openai import OpenAI
from pydantic_ai import Agent
from pydantic_ai.models.openai import OpenAIModel
from pydub import AudioSegment
from pydub.silence import split_on_silence

from config import settings
from models import (
    AnalysisResult,
    ClassificationResult,
    SQLQuery,
)

# Model configuration
DEFAULT_MODEL = "gpt-4o"

# OpenAI models
OPENAI_MODELS_LIST = [
    "gpt-4o",
    "gpt-4o-mini",
    "gpt-4-turbo",
    "gpt-4-turbo-preview",
    "gpt-4",
    "gpt-3.5-turbo",
    "o1-preview",
    "o1-mini",
]

# Together AI models
TOGETHER_MODELS_LIST = [
    # Llama models
    "meta-llama/Llama-3.3-70B-Instruct-Turbo",
    "meta-llama/Llama-3.1-70B-Instruct-Turbo",
    "meta-llama/Llama-3.1-8B-Instruct-Turbo",
    "meta-llama/Llama-3-70b-chat-hf",
    # Qwen models
    "Qwen/QwQ-32B-Preview",
    "Qwen/Qwen2.5-72B-Instruct-Turbo",
    "Qwen/Qwen2.5-32B-Instruct-Turbo",
    "Qwen/Qwen2.5-14B-Instruct-Turbo",
    "Qwen/Qwen2.5-7B-Instruct-Turbo",
    "Qwen/Qwen1.5-110B-Chat",
    # Mistral models
    "mistralai/Mixtral-8x22B-Instruct-v0.1",
    "mistralai/Mixtral-8x7B-Instruct-v0.1",
    "mistralai/Mistral-7B-Instruct-v0.3",
    # Other modern models
    "WizardLM/WizardLM-13B-V1.2",
    "togethercomputer/RedPajama-INCITE-7B-Chat",
    "togethercomputer/alpaca-7b",
]

# Prompt placeholder constants
PLACEHOLDER_USER_INPUT = "USER_INPUT:"
PLACEHOLDER_DREAMS_THOUGHTS = "INOUT DREAMS/THOUGHTS:"
PLACEHOLDER_DREAMS_CONTENT = "DREAMS TO SUMMARIZE:"


def clean_prompt(prompt: str, placeholder: str) -> str:
    """Remove placeholder lines from prompt."""
    if placeholder in prompt:
        return prompt.split(placeholder)[0].strip()
    return prompt.strip()


def get_model(model_name: str = DEFAULT_MODEL):
    """Get the appropriate model instance based on model name."""
    if model_name in TOGETHER_MODELS_LIST:
        return OpenAIModel(
            model_name,
            base_url="https://api.together.xyz/v1",
            api_key=settings.TOGETHER_API_KEY,
        )
    # Use OpenAI for OpenAI models
    if model_name in OPENAI_MODELS_LIST:
        return OpenAIModel(
            model_name,
            api_key=settings.OPENAI_API_KEY,
        )
    # Default to OpenAI for unknown models
    return OpenAIModel(
        model_name,
        api_key=settings.OPENAI_API_KEY,
    )


def create_classification_agent(model_name: str = DEFAULT_MODEL) -> Agent:
    """Create a classification agent with the specified model."""
    prompt = clean_prompt(settings.CLASSIFIER_PROMPT, PLACEHOLDER_USER_INPUT)
    return Agent(
        model=get_model(model_name),
        system_prompt=prompt,
        result_type=ClassificationResult,
    )


def create_sql_query_agent(model_name: str = DEFAULT_MODEL) -> Agent:
    """Create a SQL query generation agent with the specified model."""
    prompt = clean_prompt(settings.CUSTOM_RETRIEVER_PROMPT, PLACEHOLDER_USER_INPUT)
    return Agent(
        model=get_model(model_name),
        system_prompt=prompt,
        result_type=SQLQuery,
    )


def create_analysis_agent(model_name: str = DEFAULT_MODEL) -> Agent:
    """Create an analysis agent with the specified model."""
    prompt = clean_prompt(settings.ANALYZING_PROMPT, PLACEHOLDER_DREAMS_THOUGHTS)
    return Agent(
        model=get_model(model_name),
        system_prompt=prompt,
        result_type=AnalysisResult,
    )


def create_summarization_agent(model_name: str = DEFAULT_MODEL) -> Agent:
    """Create a summarization agent with the specified model."""
    prompt = clean_prompt(settings.SUMMARIZATION_PROMPT, PLACEHOLDER_DREAMS_CONTENT)
    # Summarization doesn't need structured output, just return text
    return Agent(
        model=get_model(model_name),
        system_prompt=prompt,
    )


def count_tokens(text: str) -> int:
    """Count tokens in text. Uses character-based estimate (tiktoken is used by RecursiveCharacterTextSplitter for chunking)."""
    # Conservative estimate: ~4 characters per token
    # RecursiveCharacterTextSplitter uses tiktoken internally for accurate chunking
    return len(text) // 4


def chunk_text(text: str, chunk_size_tokens: int = None) -> list[str]:
    """Split text into chunks using langchain's RecursiveCharacterTextSplitter."""
    if chunk_size_tokens is None:
        chunk_size_tokens = settings.CHUNK_SIZE_TOKENS
    text_splitter = RecursiveCharacterTextSplitter.from_tiktoken_encoder(
        model_name="gpt-4o",
        chunk_size=chunk_size_tokens,
        chunk_overlap=200,  # Small overlap to preserve context
    )
    chunks = text_splitter.split_text(text)
    return chunks


class LlmController:
    """Controller for AI agents using Pydantic AI."""

    def __init__(self, model_name: str = DEFAULT_MODEL):
        """Initialize the LLM controller with a specific model."""
        self.model_name = model_name
        self.openai_client = OpenAI(api_key=settings.OPENAI_API_KEY)
        # Create agents with the specified model
        self.classification_agent = create_classification_agent(model_name)
        self.sql_query_agent = create_sql_query_agent(model_name)
        self.analysis_agent = create_analysis_agent(model_name)
        self.summarization_agent = create_summarization_agent(model_name)

    async def classify_text(self, text: str) -> str:
        """Classify the text and return the type as a string."""
        result = await self.classification_agent.run(text)
        return result.data.type.value

    async def generate_sql_query(
        self, user_input: str, username: str, user_tg_id: int
    ) -> str:
        """Generate a SQL query based on user input."""
        today = datetime.datetime.today().strftime("%Y-%m-%d %H:%M:%S")
        prompt = f"{user_input} today date: {today}. User ID: {user_tg_id}, Username: {username}"
        result = await self.sql_query_agent.run(prompt)
        return result.data.query

    async def summarize_dreams(self, content: str) -> str:
        """Summarize dreams using the summarization prompt."""
        result = await self.summarization_agent.run(content)
        # Get the text response (summarization agent doesn't use structured output)
        if hasattr(result, 'data') and hasattr(result.data, 'analysis'):
            return result.data.analysis
        return str(result.data) if hasattr(result, 'data') else str(result)

    async def analyze_dreams_or_thoughts(self, content: str) -> str:
        """Analyze dreams or thoughts. If content is too long, chunk and summarize first."""
        # Count tokens
        token_count = count_tokens(content)
        
        # If content is within limit, analyze directly
        if token_count <= settings.MAX_TOKENS_FOR_ANALYSIS:
            result = await self.analysis_agent.run(content)
            return result.data.analysis
        
        # Content is too long - chunk and summarize
        chunks = chunk_text(content, settings.CHUNK_SIZE_TOKENS)
        
        # Limit to 4-5 chunks as requested
        if len(chunks) > 5:
            chunks = chunks[:5]
        
        # Summarize each chunk
        summaries = []
        for i, chunk in enumerate(chunks):
            summary = await self.summarize_dreams(chunk)
            summaries.append(f"### Summary {i+1} ###\n{summary}")
        
        # Join all summaries and analyze
        all_summaries = "\n\n".join(summaries)
        result = await self.analysis_agent.run(all_summaries)
        return result.data.analysis

    def transcribe_text(self, temp_path: str) -> str:
        """Transcribe audio file to text using Whisper.
        
        Handles large files by splitting on silence and transcribing iteratively.
        Cleans up the temporary file after transcription.
        """
        try:
            file_size_mb = os.path.getsize(temp_path) / (1024 * 1024)
            
            if file_size_mb <= settings.MAX_AUDIO_FILE_SIZE_MB:
                # File is small enough, transcribe directly
                return self._transcribe_chunk(temp_path)
            
            # File is too large, split on silence and transcribe iteratively
            return self._transcribe_large_file(temp_path)
        finally:
            # Clean up original temporary file
            if os.path.exists(temp_path):
                os.remove(temp_path)
    
    def _transcribe_chunk(self, audio_path: str) -> str:
        """Transcribe a single audio chunk."""
        with open(audio_path, "rb") as audio_file:
            transcription = self.openai_client.audio.transcriptions.create(
                model="whisper-1", file=audio_file
            )
        return transcription.text
    
    def _transcribe_large_file(self, temp_path: str) -> str:
        """Split large audio file on silence and transcribe iteratively."""
        # Load audio file
        audio = AudioSegment.from_file(temp_path)
        
        # Split on silence (min 1 second of silence, -40 dB threshold)
        chunks = split_on_silence(
            audio,
            min_silence_len=1000,  # 1 second
            silence_thresh=-40,    # dB
            keep_silence=500,      # Keep 0.5s of silence for context
        )
        
        if not chunks:
            # If no silence found, split into fixed 10-minute chunks
            chunk_length_ms = 10 * 60 * 1000  # 10 minutes
            chunks = [
                audio[i:i + chunk_length_ms]
                for i in range(0, len(audio), chunk_length_ms)
            ]
        
        # Transcribe each chunk and combine
        transcriptions = []
        temp_chunks = []
        
        try:
            for i, chunk in enumerate(chunks):
                # Export chunk to temporary file
                chunk_path = f"{temp_path}_chunk_{i}.ogg"
                chunk.export(chunk_path, format="ogg")
                temp_chunks.append(chunk_path)
                
                # Transcribe chunk
                text = self._transcribe_chunk(chunk_path)
                if text.strip():
                    transcriptions.append(text)
        
        finally:
            # Clean up temporary chunk files
            for chunk_path in temp_chunks:
                if os.path.exists(chunk_path):
                    os.remove(chunk_path)
        
        # Combine all transcriptions
        return " ".join(transcriptions)


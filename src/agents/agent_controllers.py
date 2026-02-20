import datetime
import logging
import os

from openai import OpenAI
from pydub import AudioSegment
from pydub.silence import split_on_silence

from agents.agents import (
    create_analysis_agent,
    create_classification_agent,
    create_sql_query_agent,
    create_summarization_agent,
)
from agents.utils import chunk_text
from config import settings

logger = logging.getLogger(__name__)


class LlmController:
    def __init__(self, model_name: str = settings.DEFAULT_MODEL):
        self.model_name = model_name
        self.openai_client = OpenAI(api_key=settings.OPENAI_API_KEY)
        self.classification_agent = create_classification_agent(model_name)
        self.sql_query_agent = create_sql_query_agent(model_name)
        self.analysis_agent = create_analysis_agent(model_name)
        self.summarization_agent = create_summarization_agent(model_name)

    async def classify_text(self, text: str) -> str:
        result = await self.classification_agent.run(text)
        return result.data.type.value

    async def generate_sql_query(
        self, user_input: str, username: str, user_tg_id: int
    ) -> str:
        today = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        prompt = f"{user_input} today date: {today}. User ID: {user_tg_id}, Username: {username}"

        result = await self.sql_query_agent.run(prompt)
        logger.info(f"SQL Query generated: {result}")
        return result.data.query

    async def summarize_dreams(self, content: str) -> str:
        result = await self.summarization_agent.run(content)
        if hasattr(result, "data") and hasattr(result.data, "analysis"):
            return result.data.analysis

        return str(result.data) if hasattr(result, "data") else str(result)

    async def analyze_dreams_or_thoughts(self, content: str) -> str:
        max_tokens_threshold = int(settings.MAX_TOKENS_FOR_ANALYSIS * 0.7)
        test_chunks = chunk_text(content, max_tokens_threshold, self.model_name)

        print(
            f"Content splits into {len(test_chunks)} chunk(s) at threshold {max_tokens_threshold} tokens"
        )

        if len(test_chunks) == 1:
            try:
                result = await self.analysis_agent.run(content)
                if hasattr(result, "data") and hasattr(result.data, "analysis"):
                    return result.data.analysis
                return str(result.data) if hasattr(result, "data") else str(result)
            except Exception as e:
                print(f"Direct analysis failed, falling back to chunking: {e}")

        chunk_size = min(settings.CHUNK_SIZE_TOKENS, max_tokens_threshold // 2)
        print(f"Chunking content into chunks of size: {chunk_size} tokens")
        chunks = chunk_text(content, chunk_size, self.model_name)

        if len(chunks) > 5:
            chunks = chunks[:5]
            print(f"Limited to 5 chunks (had {len(chunks)} chunks)")

        summaries = []
        for i, chunk in enumerate(chunks):
            try:
                chunk_test = chunk_text(chunk, chunk_size, self.model_name)
                chunk_count = len(chunk_test)
                print(
                    f"Summarizing chunk {i + 1}/{len(chunks)} (splits into {chunk_count} sub-chunks)"
                )
                summary = await self.summarize_dreams(chunk)
                summaries.append(f"### Summary {i + 1} ###\n{summary}")

            except Exception as e:
                print(f"Error summarizing chunk {i + 1}: {e}")
                chunk_test = chunk_text(chunk, chunk_size, self.model_name)
                if len(chunk_test) > 1:
                    truncated = chunk[: chunk_size * 4]
                    summaries.append(
                        f"### Summary {i + 1} (truncated) ###\n{truncated}"
                    )
                else:
                    summaries.append(f"### Summary {i + 1} ###\n{chunk[:500]}...")

        all_summaries = "\n\n".join(summaries)
        summary_chunks = chunk_text(
            all_summaries, max_tokens_threshold, self.model_name
        )
        print(
            f"Total summaries split into {len(summary_chunks)} chunk(s) at threshold {max_tokens_threshold} tokens"
        )

        if len(summary_chunks) > 1:
            all_summaries = summary_chunks[0]
            print("Truncated summaries to fit in one chunk")

        try:
            result = await self.analysis_agent.run(all_summaries)
            if hasattr(result, "data") and hasattr(result.data, "analysis"):
                return result.data.analysis
            return str(result.data) if hasattr(result, "data") else str(result)
        except Exception as e:
            print(f"Analysis failed after chunking: {e}")
            return (
                f"Analysis completed but encountered formatting issues. "
                f"Found {len(chunks)} chunks of content. Error: {str(e)}"
            )

    def transcribe_text(self, temp_path: str) -> str:
        try:
            file_size_mb = os.path.getsize(temp_path) / (1024 * 1024)

            if file_size_mb <= settings.MAX_AUDIO_FILE_SIZE_MB:
                return self._transcribe_chunk(temp_path)

            return self._transcribe_large_file(temp_path)
        finally:
            if os.path.exists(temp_path):
                os.remove(temp_path)

    def _transcribe_chunk(self, audio_path: str) -> str:
        with open(audio_path, "rb") as audio_file:
            transcription = self.openai_client.audio.transcriptions.create(
                model=settings.AUDIO_TRANSCRIPTION_MODEL, file=audio_file
            )
        return transcription.text

    def _transcribe_large_file(self, temp_path: str) -> str:
        audio = AudioSegment.from_file(temp_path)

        chunks = split_on_silence(
            audio,
            min_silence_len=settings.AUDIO_SILENCE_MIN_LEN_MS,
            silence_thresh=settings.AUDIO_SILENCE_THRESH_DB,
            keep_silence=settings.AUDIO_KEEP_SILENCE_MS,
        )

        if not chunks:
            chunk_length_ms = settings.AUDIO_FALLBACK_CHUNK_MIN * 60 * 1000
            chunks = [
                audio[i : i + chunk_length_ms]
                for i in range(0, len(audio), chunk_length_ms)
            ]

        transcriptions = []
        temp_chunks = []

        try:
            for i, chunk in enumerate(chunks):
                chunk_path = f"{temp_path}_chunk_{i}.ogg"
                chunk.export(chunk_path, format="ogg")
                temp_chunks.append(chunk_path)

                text = self._transcribe_chunk(chunk_path)
                if text.strip():
                    transcriptions.append(text)

        finally:
            for chunk_path in temp_chunks:
                if os.path.exists(chunk_path):
                    os.remove(chunk_path)

        return " ".join(transcriptions)

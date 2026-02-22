from unittest.mock import AsyncMock, MagicMock, Mock, patch

import pytest

from agents.agent_controllers import LlmController


@pytest.fixture
def controller():
    with (
        patch("agents.agent_controllers.OpenAI"),
        patch("agents.agent_controllers.create_classification_agent"),
        patch("agents.agent_controllers.create_sql_query_agent"),
        patch("agents.agent_controllers.create_analysis_agent"),
        patch("agents.agent_controllers.create_summarization_agent"),
    ):
        return LlmController(model_name="gpt-4o-mini")


class TestClassifyText:
    async def test_returns_type_value(self, controller):
        mock_result = MagicMock()
        mock_result.data.type.value = "dream"
        controller.classification_agent.run = AsyncMock(return_value=mock_result)

        result = await controller.classify_text("I had a flying dream last night")

        assert result == "dream"

    async def test_passes_text_to_agent(self, controller):
        mock_result = MagicMock()
        mock_result.data.type.value = "thought"
        controller.classification_agent.run = AsyncMock(return_value=mock_result)

        await controller.classify_text("some text")

        controller.classification_agent.run.assert_awaited_once_with("some text")

    @pytest.mark.parametrize(
        "type_value", ["dream", "thought", "plans", "retreive", "analyze"]
    )
    async def test_all_classification_types_passed_through(
        self, controller, type_value
    ):
        mock_result = MagicMock()
        mock_result.data.type.value = type_value
        controller.classification_agent.run = AsyncMock(return_value=mock_result)

        result = await controller.classify_text("text")

        assert result == type_value


class TestGenerateSqlQuery:
    async def test_returns_query_string(self, controller):
        mock_result = MagicMock()
        mock_result.data.query = "SELECT * FROM thoughts WHERE user_tg_id = 42"
        controller.sql_query_agent.run = AsyncMock(return_value=mock_result)

        result = await controller.generate_sql_query("show my dreams", "alice", 42)

        assert result == "SELECT * FROM thoughts WHERE user_tg_id = 42"

    async def test_prompt_includes_username_and_id(self, controller):
        mock_result = MagicMock()
        mock_result.data.query = "SELECT 1"
        controller.sql_query_agent.run = AsyncMock(return_value=mock_result)

        await controller.generate_sql_query("show my dreams", "alice", 42)

        prompt = controller.sql_query_agent.run.call_args[0][0]
        assert "alice" in prompt
        assert "42" in prompt

    async def test_prompt_includes_current_date(self, controller):
        mock_result = MagicMock()
        mock_result.data.query = "SELECT 1"
        controller.sql_query_agent.run = AsyncMock(return_value=mock_result)

        await controller.generate_sql_query("show my dreams", "bob", 1)

        prompt = controller.sql_query_agent.run.call_args[0][0]
        assert "2026" in prompt  # current year


class TestAnalyzeDreams:
    async def test_single_chunk_returns_analysis(self, controller):
        mock_result = MagicMock()
        mock_result.data.analysis = "BAN. KAI."
        controller.analysis_agent.run = AsyncMock(return_value=mock_result)

        with patch(
            "agents.agent_controllers.chunk_text", return_value=["single chunk"]
        ):
            result = await controller.analyze_dreams_or_thoughts("some dream content")

        assert result == "BAN. KAI."

    @patch(
        "agents.agent_controllers.chunk_text",
        new_callable=Mock,
        return_value=["whatewer"],
    )
    @patch(
        "agents.agent_controllers.LlmController.summarize_dreams",
        new_callable=AsyncMock,
        return_value="AMATERASU",
    )
    async def test_analysis_agent_receives_original_content(
        self,
        mock_summarize: Mock,
        mock_chunk: AsyncMock,
        controller: LlmController,
    ):

        mock_result = MagicMock()
        controller.analysis_agent.run = AsyncMock(return_value=mock_result)

        await controller.analyze_dreams_or_thoughts("Whatever is here it's mocked")

        controller.analysis_agent.run.assert_awaited_once_with(
            "### Summary 1 ###\nAMATERASU"
        )


class TestTranscribeText:
    def test_small_file_returns_transcription(self, controller, tmp_path, monkeypatch):
        audio_file = tmp_path / "audio.ogg"
        audio_file.write_bytes(b"fake audio bytes")

        mock_settings = MagicMock()
        mock_settings.MAX_AUDIO_FILE_SIZE_MB = 25
        mock_settings.AUDIO_TRANSCRIPTION_MODEL = "whisper-1"
        monkeypatch.setattr("agents.agent_controllers.settings", mock_settings)

        mock_transcription = MagicMock()
        mock_transcription.text = "hello world"
        controller.openai_client.audio.transcriptions.create.return_value = (
            mock_transcription
        )

        result = controller.transcribe_text(str(audio_file))

        assert result == "hello world"

    def test_temp_file_deleted_after_transcription(
        self, controller, tmp_path, monkeypatch
    ):
        audio_file = tmp_path / "audio.ogg"
        audio_file.write_bytes(b"fake audio bytes")

        mock_settings = MagicMock()
        mock_settings.MAX_AUDIO_FILE_SIZE_MB = 25
        mock_settings.AUDIO_TRANSCRIPTION_MODEL = "whisper-1"
        monkeypatch.setattr("agents.agent_controllers.settings", mock_settings)

        controller.openai_client.audio.transcriptions.create.return_value = MagicMock(
            text="ok"
        )

        controller.transcribe_text(str(audio_file))

        assert not audio_file.exists()

    def test_temp_file_deleted_even_on_error(self, controller, tmp_path, monkeypatch):
        audio_file = tmp_path / "audio.ogg"
        audio_file.write_bytes(b"data")

        mock_settings = MagicMock()
        mock_settings.MAX_AUDIO_FILE_SIZE_MB = 25
        mock_settings.AUDIO_TRANSCRIPTION_MODEL = "whisper-1"
        monkeypatch.setattr("agents.agent_controllers.settings", mock_settings)

        controller.openai_client.audio.transcriptions.create.side_effect = RuntimeError(
            "API error"
        )

        with pytest.raises(RuntimeError, match="API error"):
            controller.transcribe_text(str(audio_file))

        assert not audio_file.exists()

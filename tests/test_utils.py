from unittest.mock import MagicMock, patch

import pytest

from agents.utils import chunk_text, clean_prompt, get_model


class TestCleanPrompt:
    def test_splits_on_placeholder(self):
        prompt = "You are an assistant. {user_input} Please respond."
        assert clean_prompt(prompt, "{user_input}") == "You are an assistant."

    def test_returns_stripped_string_when_placeholder_absent(self):
        assert clean_prompt("  You are an assistant.  ", "{user_input}") == "You are an assistant."

    def test_empty_prompt(self):
        assert clean_prompt("", "{user_input}") == ""

    def test_placeholder_at_start_returns_empty(self):
        assert clean_prompt("{user_input} is the user message", "{user_input}") == ""

    @pytest.mark.parametrize("placeholder", ["{user_input}", "USER_TEXT", "<<<INPUT>>>"])
    def test_various_placeholder_formats(self, placeholder):
        prompt = f"System preamble. {placeholder} Ignore everything after."
        result = clean_prompt(prompt, placeholder)
        assert "Ignore everything after" not in result
        assert "System preamble" in result


class TestChunkText:
    def test_short_text_returns_single_chunk(self):
        text = "This is a short sentence."
        chunks = chunk_text(text, chunk_size_tokens=512, model_name="gpt-4")
        assert len(chunks) == 1
        assert chunks[0] == text

    def test_long_text_returns_multiple_chunks(self):
        text = "word " * 2000
        chunks = chunk_text(text, chunk_size_tokens=300, model_name="gpt-4")
        assert len(chunks) > 1

    def test_all_words_preserved_across_chunks(self):
        words = [f"uniqueword{i}" for i in range(200)]
        chunks = chunk_text(" ".join(words), chunk_size_tokens=250, model_name="gpt-4")
        combined = " ".join(chunks)
        for word in words:
            assert word in combined

    def test_empty_text_returns_empty_list(self):
        assert chunk_text("", chunk_size_tokens=512, model_name="gpt-4") == []


class TestGetModel:
    @pytest.fixture
    def mock_settings(self, monkeypatch):
        s = MagicMock()
        s.TOGETHER_MODELS_LIST = ["together/llama-3"]
        s.OPENAI_MODELS_LIST = ["gpt-4o", "gpt-4o-mini"]
        s.TOGETHER_API_KEY = "together-key"
        s.OPENAI_API_KEY = "openai-key"
        monkeypatch.setattr("agents.utils.settings", s)
        return s

    def test_together_model_uses_together_base_url(self, mock_settings):
        with patch("agents.utils.OpenAIModel") as MockModel:
            get_model("together/llama-3")
            MockModel.assert_called_once_with(
                "together/llama-3",
                base_url="https://api.together.xyz/v1",
                api_key="together-key",
            )

    def test_openai_model_uses_openai_api_key(self, mock_settings):
        with patch("agents.utils.OpenAIModel") as MockModel:
            get_model("gpt-4o")
            MockModel.assert_called_once_with("gpt-4o", api_key="openai-key")

    def test_unknown_model_falls_back_to_openai(self, mock_settings):
        with patch("agents.utils.OpenAIModel") as MockModel:
            get_model("some-unknown-model")
            MockModel.assert_called_once_with("some-unknown-model", api_key="openai-key")
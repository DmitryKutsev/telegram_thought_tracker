import pytest
from pydantic import ValidationError

from agents.models import (
    AnalysisResult,
    ClassificationResult,
    MessageType,
    QueryParams,
    SQLQuery,
)


class TestMessageType:
    def test_all_values_defined(self):
        assert {e.value for e in MessageType} == {"dream", "thought", "plans", "retreive", "analyze"}

    @pytest.mark.parametrize("value,expected", [
        ("dream", MessageType.DREAM),
        ("thought", MessageType.THOUGHT),
        ("plans", MessageType.PLANS),
        ("retreive", MessageType.RETRIEVE),
        ("analyze", MessageType.ANALYZE),
    ])
    def test_value_lookup(self, value, expected):
        assert MessageType(value) == expected

    def test_invalid_value_raises(self):
        with pytest.raises(ValueError):
            MessageType("invalid")


class TestClassificationResult:
    def test_type_only(self):
        result = ClassificationResult(type=MessageType.DREAM)
        assert result.type == MessageType.DREAM
        assert result.confidence is None

    def test_with_confidence(self):
        result = ClassificationResult(type=MessageType.ANALYZE, confidence="high")
        assert result.confidence == "high"

    def test_invalid_type_raises(self):
        with pytest.raises(ValidationError):
            ClassificationResult(type="not_a_type")


class TestSQLQuery:
    def test_stores_query_string(self):
        q = SQLQuery(query="SELECT * FROM thoughts WHERE user_tg_id = 1")
        assert "thoughts" in q.query

    def test_empty_query_allowed(self):
        q = SQLQuery(query="")
        assert q.query == ""


class TestQueryParams:
    def test_dates_are_optional(self):
        params = QueryParams(type="dream")
        assert params.start_date is None
        assert params.end_date is None

    def test_with_date_range(self):
        params = QueryParams(
            type="thought",
            start_date="2024-01-01 00:00:00",
            end_date="2024-12-31 23:59:59",
        )
        assert params.start_date == "2024-01-01 00:00:00"
        assert params.end_date == "2024-12-31 23:59:59"

    def test_missing_type_raises(self):
        with pytest.raises(ValidationError):
            QueryParams()


class TestAnalysisResult:
    def test_analysis_only(self):
        result = AnalysisResult(analysis="Water symbolizes the unconscious.")
        assert result.key_symbols is None
        assert result.emotional_tone is None

    def test_with_all_fields(self):
        result = AnalysisResult(
            analysis="Shadow archetype manifests as the stranger.",
            key_symbols=["shadow", "water", "descent"],
            emotional_tone="melancholic",
        )
        assert len(result.key_symbols) == 3
        assert result.emotional_tone == "melancholic"

    def test_missing_analysis_raises(self):
        with pytest.raises(ValidationError):
            AnalysisResult()
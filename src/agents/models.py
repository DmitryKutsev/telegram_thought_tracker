from enum import Enum

from pydantic import BaseModel, Field


class MessageType(str, Enum):
    DREAM = "dream"
    THOUGHT = "thought"
    PLANS = "plans"
    RETRIEVE = "retreive"
    ANALYZE = "analyze"


class ClassificationResult(BaseModel):
    type: MessageType = Field(description="The classified type of the message")
    confidence: str | None = Field(default=None, description="Confidence level or reasoning")


class QueryParams(BaseModel):
    type: str = Field(description="Type of thoughts to retrieve: 'dream', 'thought', or 'plans'")
    start_date: str | None = Field(default=None, description="Start date in %Y-%m-%d %H:%M:%S format")
    end_date: str | None = Field(default=None, description="End date in %Y-%m-%d %H:%M:%S format")


class SQLQuery(BaseModel):
    query: str = Field(description="Raw SQL query string ready for execution")


class AnalysisResult(BaseModel):
    analysis: str = Field(description="Jungian psychoanalytic analysis of the content")
    key_symbols: list[str] | None = Field(default=None, description="Key symbols or archetypes identified")
    emotional_tone: str | None = Field(default=None, description="Overall emotional tone detected")
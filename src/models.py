"""Pydantic models for structured AI outputs."""

from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field


class MessageType(str, Enum):
    """Type of message classification."""

    DREAM = "dream"
    THOUGHT = "thought"
    PLANS = "plans"
    RETRIEVE = "retreive"
    ANALYZE = "analyze"


class ClassificationResult(BaseModel):
    """Result of message classification."""

    type: MessageType = Field(description="The classified type of the message")
    confidence: Optional[str] = Field(
        default=None, description="Confidence level or reasoning"
    )


class QueryParams(BaseModel):
    """Parameters for database query retrieval."""

    type: str = Field(description="Type of thoughts to retrieve: 'dream', 'thought', or 'plans'")
    start_date: Optional[str] = Field(
        default=None, description="Start date in %Y-%m-%d %H:%M:%S format"
    )
    end_date: Optional[str] = Field(
        default=None, description="End date in %Y-%m-%d %H:%M:%S format"
    )


class SQLQuery(BaseModel):
    """SQL query for database operations."""

    query: str = Field(description="Raw SQL query string ready for execution")


class AnalysisResult(BaseModel):
    """Result of dream/thought analysis."""

    analysis: str = Field(description="Jungian psychoanalytic analysis of the content")
    key_symbols: Optional[list[str]] = Field(
        default=None, description="Key symbols or archetypes identified"
    )
    emotional_tone: Optional[str] = Field(
        default=None, description="Overall emotional tone detected"
    )


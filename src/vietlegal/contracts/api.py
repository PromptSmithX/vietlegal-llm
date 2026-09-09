"""Strict API payload contracts; FastAPI routing is intentionally deferred to Phase 8."""

from __future__ import annotations

from datetime import date, datetime
from enum import StrEnum
from typing import Self

from pydantic import Field, HttpUrl, field_validator, model_validator

from .data import IDENTIFIER_PATTERN, DocumentType, StrictModel

ABSTENTION_MESSAGE = (
    "Các căn cứ được truy xuất hiện chưa đủ để đưa ra kết luận chắc chắn cho trường hợp này."
)
CITATION_ID_PATTERN = r"^C[1-5]$"
REQUEST_ID_PATTERN = r"^[A-Za-z0-9][A-Za-z0-9_.\-]{2,127}$"


class ChatStatus(StrEnum):
    ANSWERED = "answered"
    INSUFFICIENT_CONTEXT = "insufficient_context"


class HealthStatus(StrEnum):
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"


class Citation(StrictModel):
    citation_id: str = Field(pattern=CITATION_ID_PATTERN)
    document_id: str = Field(pattern=IDENTIFIER_PATTERN)
    chunk_id: str = Field(pattern=IDENTIFIER_PATTERN)
    document_number: str = Field(min_length=1, max_length=100)
    document_title: str = Field(min_length=1, max_length=500)
    article: str | None = Field(default=None, max_length=100)
    clause: str | None = Field(default=None, max_length=100)
    point: str | None = Field(default=None, max_length=100)
    excerpt: str = Field(min_length=1)
    effective_from: date
    effective_to: date | None = None
    source_url: HttpUrl

    @model_validator(mode="after")
    def validate_effective_interval(self) -> Self:
        if self.effective_to is not None and self.effective_to <= self.effective_from:
            raise ValueError("effective_to must be later than effective_from")
        return self


class TextRequest(StrictModel):
    @staticmethod
    def _normalize_text(value: str) -> str:
        return " ".join(value.split())


class ChatRequest(TextRequest):
    question: str = Field(min_length=1, max_length=2_000)
    reference_date: date | None = None

    @field_validator("question", mode="before")
    @classmethod
    def normalize_question(cls, value: str) -> str:
        return cls._normalize_text(value)


class SearchRequest(TextRequest):
    query: str = Field(min_length=1, max_length=2_000)
    reference_date: date | None = None
    limit: int = Field(default=5, ge=1, le=20)

    @field_validator("query", mode="before")
    @classmethod
    def normalize_query(cls, value: str) -> str:
        return cls._normalize_text(value)


class ChatAnswer(StrictModel):
    conclusion: str = Field(min_length=1)
    analysis: str = Field(min_length=1)
    legal_basis: list[str]
    notes: str = Field(min_length=1)


class ChatResponse(StrictModel):
    request_id: str = Field(pattern=REQUEST_ID_PATTERN)
    status: ChatStatus
    reference_date: date
    answer: ChatAnswer
    citations: list[Citation] = Field(default_factory=list)

    @model_validator(mode="after")
    def validate_status_contract(self) -> Self:
        if self.status is ChatStatus.ANSWERED and not self.citations:
            raise ValueError("answered responses require at least one citation")
        if (
            self.status is ChatStatus.INSUFFICIENT_CONTEXT
            and self.answer.conclusion != ABSTENTION_MESSAGE
        ):
            raise ValueError(
                "insufficient_context responses must use the standard abstention message"
            )
        return self


class SearchResult(StrictModel):
    rank: int = Field(ge=1)
    citation: Citation
    score: float


class SearchResponse(StrictModel):
    request_id: str = Field(pattern=REQUEST_ID_PATTERN)
    reference_date: date
    results: list[SearchResult]


class DocumentVersionSummary(StrictModel):
    version_id: str = Field(pattern=IDENTIFIER_PATTERN)
    retrieved_at: datetime


class DocumentDetails(StrictModel):
    document_id: str = Field(pattern=IDENTIFIER_PATTERN)
    document_number: str = Field(min_length=1, max_length=100)
    title: str = Field(min_length=1, max_length=500)
    document_type: DocumentType
    issuer: str = Field(min_length=1, max_length=300)
    issued_date: date
    primary_source_url: HttpUrl
    versions: list[DocumentVersionSummary]


class DocumentResponse(StrictModel):
    request_id: str = Field(pattern=REQUEST_ID_PATTERN)
    document: DocumentDetails


class HealthResponse(StrictModel):
    status: HealthStatus
    checks: dict[str, str]
    versions: dict[str, str]


class ErrorDetail(StrictModel):
    code: str = Field(pattern=r"^[A-Z][A-Z0-9_]*$")
    message: str = Field(min_length=1, max_length=1_000)
    details: dict[str, object] = Field(default_factory=dict)
    request_id: str = Field(pattern=REQUEST_ID_PATTERN)


class ErrorResponse(StrictModel):
    error: ErrorDetail

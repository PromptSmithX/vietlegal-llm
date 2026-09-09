"""Versioned domain and API contracts."""

from .api import (
    ABSTENTION_MESSAGE,
    ChatAnswer,
    ChatRequest,
    ChatResponse,
    Citation,
    DocumentResponse,
    ErrorResponse,
    HealthResponse,
    SearchRequest,
    SearchResponse,
)
from .data import (
    ArtifactMetadata,
    DocumentRelation,
    DocumentType,
    LegalChunk,
    LegalDocument,
    LegalProvision,
    RelationType,
    ValidityStatus,
)

__all__ = [
    "ABSTENTION_MESSAGE",
    "ArtifactMetadata",
    "ChatAnswer",
    "ChatRequest",
    "ChatResponse",
    "Citation",
    "DocumentRelation",
    "DocumentResponse",
    "DocumentType",
    "ErrorResponse",
    "HealthResponse",
    "LegalChunk",
    "LegalDocument",
    "LegalProvision",
    "RelationType",
    "SearchRequest",
    "SearchResponse",
    "ValidityStatus",
]

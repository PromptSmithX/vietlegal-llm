"""Canonical, strict data contracts for versioned legal-corpus artifacts."""

from __future__ import annotations

from datetime import date, datetime
from enum import StrEnum
from typing import Self

from pydantic import BaseModel, ConfigDict, Field, HttpUrl, field_validator, model_validator

IDENTIFIER_PATTERN = r"^[A-Za-z0-9][A-Za-z0-9_:@.\-]*$"
DOCUMENT_NUMBER_PATTERN = r"^[0-9A-Z][0-9A-Z./\-]*$"
SHA256_PATTERN = r"^[a-f0-9]{64}$"
COMMIT_HASH_PATTERN = r"^[a-f0-9]{7,64}$"


class StrictModel(BaseModel):
    """Base model that rejects contract drift and normalizes surrounding whitespace."""

    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True, validate_assignment=True)


class DocumentType(StrEnum):
    CONSTITUTION = "constitution"
    CODE = "code"
    LAW = "law"
    RESOLUTION = "resolution"
    DECREE = "decree"
    DECISION = "decision"
    CIRCULAR = "circular"
    JOINT_CIRCULAR = "joint_circular"
    CONSOLIDATED_TEXT = "consolidated_text"
    OTHER = "other"


class ValidityStatus(StrEnum):
    NOT_YET_EFFECTIVE = "not_yet_effective"
    EFFECTIVE = "effective"
    PARTIALLY_EFFECTIVE = "partially_effective"
    EXPIRED = "expired"
    UNKNOWN = "unknown"


class RelationType(StrEnum):
    AMENDS = "amends"
    AMENDED_BY = "amended_by"
    REPLACES = "replaces"
    REPLACED_BY = "replaced_by"
    CONSOLIDATES = "consolidates"
    GUIDED_BY = "guided_by"
    GUIDES = "guides"


class DocumentRelation(StrictModel):
    type: RelationType
    target_document_id: str = Field(pattern=IDENTIFIER_PATTERN)
    source_url: HttpUrl


class LegalDocument(StrictModel):
    document_id: str = Field(pattern=IDENTIFIER_PATTERN)
    document_number: str = Field(pattern=DOCUMENT_NUMBER_PATTERN)
    title: str = Field(min_length=1, max_length=500)
    document_type: DocumentType
    issuer: str = Field(min_length=1, max_length=300)
    issued_date: date
    jurisdiction: str = Field(min_length=2, max_length=16)
    primary_source_url: HttpUrl

    @field_validator("document_number", mode="before")
    @classmethod
    def normalize_document_number(cls, value: str) -> str:
        return "".join(value.upper().split())


class DocumentVersion(StrictModel):
    version_id: str = Field(pattern=IDENTIFIER_PATTERN)
    document_id: str = Field(pattern=IDENTIFIER_PATTERN)
    retrieved_at: datetime
    content_sha256: str = Field(pattern=SHA256_PATTERN)
    parser_version: str = Field(min_length=1, max_length=100)
    manifest_version: str = Field(min_length=1, max_length=100)
    source_artifacts: list[str] = Field(min_length=1)
    relations: list[DocumentRelation] = Field(default_factory=list)


class TemporalApplicability(StrictModel):
    effective_from: date
    effective_to: date | None = None
    validity_status: ValidityStatus

    @model_validator(mode="after")
    def validate_effective_interval(self) -> Self:
        if self.effective_to is not None and self.effective_to <= self.effective_from:
            raise ValueError("effective_to must be later than effective_from")
        return self

    def is_effective_on(self, reference_date: date) -> bool:
        return (
            self.validity_status is ValidityStatus.EFFECTIVE
            and self.effective_from <= reference_date
            and (self.effective_to is None or reference_date < self.effective_to)
        )


class LegalProvision(TemporalApplicability):
    provision_id: str = Field(pattern=IDENTIFIER_PATTERN)
    version_id: str = Field(pattern=IDENTIFIER_PATTERN)
    chapter: str | None = Field(default=None, max_length=200)
    section: str | None = Field(default=None, max_length=200)
    article: str | None = Field(default=None, max_length=100)
    clause: str | None = Field(default=None, max_length=100)
    point: str | None = Field(default=None, max_length=100)
    heading: str | None = Field(default=None, max_length=500)
    text: str = Field(min_length=1)
    validity_source_url: HttpUrl


class LegalChunk(TemporalApplicability):
    chunk_id: str = Field(pattern=IDENTIFIER_PATTERN)
    document_id: str = Field(pattern=IDENTIFIER_PATTERN)
    version_id: str = Field(pattern=IDENTIFIER_PATTERN)
    provision_ids: list[str] = Field(min_length=1)
    display_header: str = Field(min_length=1, max_length=1_000)
    text: str = Field(min_length=1)
    source_url: HttpUrl
    content_sha256: str = Field(pattern=SHA256_PATTERN)
    oversized: bool = False


class ArtifactMetadata(StrictModel):
    artifact_type: str = Field(min_length=1, max_length=100)
    version: str = Field(min_length=1, max_length=100)
    created_at: datetime
    source_versions: dict[str, str]
    config_hash: str = Field(pattern=SHA256_PATTERN)
    commit_hash: str = Field(pattern=COMMIT_HASH_PATTERN)

from __future__ import annotations

from datetime import UTC, date, datetime

import pytest
from pydantic import ValidationError

from vietlegal.contracts.data import (
    ArtifactMetadata,
    DocumentType,
    LegalChunk,
    LegalDocument,
    LegalProvision,
    ValidityStatus,
)


def test_document_number_is_normalized_and_unknown_fields_are_rejected() -> None:
    document = LegalDocument.model_validate(
        {
            "document_id": "vn_bll_45_2019_qh14",
            "document_number": " 45 /2019/qh14 ",
            "title": "Bộ luật Lao động",
            "document_type": DocumentType.CODE,
            "issuer": "Quốc hội",
            "issued_date": date(2019, 11, 20),
            "jurisdiction": "VN",
            "primary_source_url": "https://vbpl.vn/example",
        }
    )
    assert document.document_number == "45/2019/QH14"

    with pytest.raises(ValidationError):
        LegalDocument.model_validate({**document.model_dump(), "unexpected": True})


def test_temporal_contracts_use_a_half_open_interval() -> None:
    provision = LegalProvision.model_validate(
        {
            "provision_id": "vn_bll_45_2019_qh14:article-46:clause-1",
            "version_id": "vn_bll_45_2019_qh14@2026-09-09:abc123",
            "chapter": "Chương III",
            "section": None,
            "article": "Điều 46",
            "clause": "Khoản 1",
            "point": None,
            "heading": "Trợ cấp thôi việc",
            "text": "Nội dung quy định.",
            "effective_from": date(2021, 1, 1),
            "effective_to": date(2027, 1, 1),
            "validity_status": ValidityStatus.EFFECTIVE,
            "validity_source_url": "https://vbpl.vn/example",
        }
    )
    assert provision.is_effective_on(date(2021, 1, 1))
    assert not provision.is_effective_on(date(2027, 1, 1))

    chunk = LegalChunk.model_validate(
        {
            "chunk_id": "vn_bll_45_2019_qh14:article-46:clause-1__abc123",
            "document_id": "vn_bll_45_2019_qh14",
            "version_id": "vn_bll_45_2019_qh14@2026-09-09:abc123",
            "provision_ids": [provision.provision_id],
            "display_header": "Bộ luật Lao động | Điều 46 | Khoản 1",
            "text": "Nội dung quy định.",
            "effective_from": date(2021, 1, 1),
            "effective_to": None,
            "validity_status": ValidityStatus.PARTIALLY_EFFECTIVE,
            "source_url": "https://vbpl.vn/example",
            "content_sha256": "a" * 64,
        }
    )
    assert not chunk.is_effective_on(date(2026, 1, 1))


def test_invalid_intervals_and_artifact_metadata_are_validated() -> None:
    with pytest.raises(ValidationError, match="effective_to"):
        LegalProvision.model_validate(
            {
                "provision_id": "vn_bll_45_2019_qh14:article-46",
                "version_id": "version",
                "text": "text",
                "effective_from": date(2021, 1, 1),
                "effective_to": date(2021, 1, 1),
                "validity_status": ValidityStatus.EFFECTIVE,
                "validity_source_url": "https://vbpl.vn/example",
            }
        )

    metadata = ArtifactMetadata(
        artifact_type="corpus",
        version="legal-corpus-v1",
        created_at=datetime(2026, 9, 9, tzinfo=UTC),
        source_versions={"manifest": "labor-sources-v1"},
        config_hash="b" * 64,
        commit_hash="abcdef1",
    )
    assert metadata.version == "legal-corpus-v1"

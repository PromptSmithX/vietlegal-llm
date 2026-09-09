from __future__ import annotations

from datetime import date

from vietlegal.contracts import (
    Citation,
    DocumentResponse,
    ErrorResponse,
    HealthResponse,
    SearchResponse,
)
from vietlegal.contracts.api import HealthStatus


def test_api_examples_instantiate_representative_contracts(citation: Citation) -> None:
    search_response = SearchResponse.model_validate(
        {
            "request_id": "req_01_example",
            "reference_date": date(2026, 9, 9),
            "results": [{"rank": 1, "citation": citation, "score": 0.8123}],
        }
    )
    assert search_response.results[0].score == 0.8123

    document_response = DocumentResponse.model_validate(
        {
            "request_id": "req_01_example",
            "document": {
                "document_id": "vn_bll_45_2019_qh14",
                "document_number": "45/2019/QH14",
                "title": "Bộ luật Lao động",
                "document_type": "code",
                "issuer": "Quốc hội",
                "issued_date": "2019-11-20",
                "primary_source_url": "https://vbpl.vn/example",
                "versions": [
                    {
                        "version_id": "vn_bll_45_2019_qh14@2026-09-09:abc123",
                        "retrieved_at": "2026-09-09T04:00:00Z",
                    }
                ],
            },
        }
    )
    assert document_response.document.document_id == "vn_bll_45_2019_qh14"

    health = HealthResponse(
        status=HealthStatus.HEALTHY,
        checks={"generator": "ok", "retriever": "ok", "corpus_index_match": "ok"},
        versions={"api": "v1", "corpus": "legal-corpus-v1"},
    )
    assert health.status is HealthStatus.HEALTHY

    error = ErrorResponse.model_validate(
        {
            "error": {
                "code": "INVALID_REFERENCE_DATE",
                "message": "reference_date không hợp lệ hoặc mâu thuẫn với câu hỏi.",
                "details": {},
                "request_id": "req_01_example",
            }
        }
    )
    assert error.error.code == "INVALID_REFERENCE_DATE"

from __future__ import annotations

from datetime import date

import pytest

from vietlegal.contracts import Citation


@pytest.fixture
def citation() -> Citation:
    return Citation.model_validate(
        {
            "citation_id": "C1",
            "document_id": "vn_bll_45_2019_qh14",
            "chunk_id": "vn_bll_45_2019_qh14:article-46:clause-1__abc123",
            "document_number": "45/2019/QH14",
            "document_title": "Bộ luật Lao động",
            "article": "Điều 46",
            "clause": "Khoản 1",
            "point": None,
            "excerpt": "Người sử dụng lao động có trách nhiệm chi trả trợ cấp thôi việc.",
            "effective_from": date(2021, 1, 1),
            "effective_to": None,
            "source_url": "https://vbpl.vn/example",
        }
    )

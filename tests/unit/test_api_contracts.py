from __future__ import annotations

from datetime import date

import pytest
from pydantic import ValidationError

from vietlegal.contracts import (
    ABSTENTION_MESSAGE,
    ChatAnswer,
    ChatRequest,
    ChatResponse,
    Citation,
    SearchRequest,
)
from vietlegal.contracts.api import ChatStatus


def test_request_text_is_normalized_and_search_limits_are_enforced() -> None:
    request = ChatRequest(question="  Tôi\nnghỉ việc   có được trợ cấp không?  ")
    assert request.question == "Tôi nghỉ việc có được trợ cấp không?"
    assert SearchRequest(query="Điều 46").limit == 5

    with pytest.raises(ValidationError):
        SearchRequest(query="Điều 46", limit=21)


def test_answered_response_requires_a_citation(citation: Citation) -> None:
    answer = ChatAnswer(
        conclusion="Có thể được hưởng trợ cấp thôi việc. [C1]",
        analysis="Cần đối chiếu điều kiện cụ thể. [C1]",
        legal_basis=["[C1] Điều 46 Bộ luật Lao động"],
        notes="Nội dung chỉ hỗ trợ nghiên cứu.",
    )
    with pytest.raises(ValidationError, match="at least one citation"):
        ChatResponse(
            request_id="req_001",
            status=ChatStatus.ANSWERED,
            reference_date=date(2026, 9, 9),
            answer=answer,
            citations=[],
        )

    response = ChatResponse(
        request_id="req_001",
        status=ChatStatus.ANSWERED,
        reference_date=date(2026, 9, 9),
        answer=answer,
        citations=[citation],
    )
    assert response.status is ChatStatus.ANSWERED


def test_insufficient_context_uses_the_standard_message() -> None:
    answer = ChatAnswer(
        conclusion=ABSTENTION_MESSAGE,
        analysis="Chưa có căn cứ đủ mạnh để kết luận.",
        legal_basis=[],
        notes="Cần bổ sung tình tiết hoặc phạm vi câu hỏi.",
    )
    response = ChatResponse(
        request_id="req_002",
        status=ChatStatus.INSUFFICIENT_CONTEXT,
        reference_date=date(2026, 9, 9),
        answer=answer,
    )
    assert response.citations == []

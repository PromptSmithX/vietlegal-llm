# API Specification — MVP v1

## 1. Quy ước chung

- Base path: `/api`.
- Content type: `application/json; charset=utf-8`.
- Ngày: ISO 8601 `YYYY-MM-DD`.
- API stateless, không streaming, không authentication trong MVP.
- Server tạo `request_id` cho mọi request; chấp nhận `X-Request-ID` hợp lệ từ client nhưng phải chống trùng.
- Unknown fields trong request bị từ chối để phát hiện client/schema drift.

## 2. Shared types

### `Citation`

```json
{
  "citation_id": "C1",
  "document_id": "vn_bll_45_2019_qh14",
  "chunk_id": "vn_bll_45_2019_qh14:article-46:clause-1__abc123",
  "document_number": "45/2019/QH14",
  "document_title": "Bộ luật Lao động",
  "article": "Điều 46",
  "clause": "Khoản 1",
  "point": null,
  "excerpt": "...",
  "effective_from": "2021-01-01",
  "effective_to": null,
  "source_url": "https://vbpl.vn/..."
}
```

### `ErrorResponse`

```json
{
  "error": {
    "code": "INVALID_REFERENCE_DATE",
    "message": "reference_date không hợp lệ hoặc mâu thuẫn với câu hỏi.",
    "details": {},
    "request_id": "req_01..."
  }
}
```

Không đưa stack trace, prompt, filesystem path, secret hoặc chain-of-thought vào lỗi.

## 3. `POST /api/chat`

### Request

```json
{
  "question": "Tôi nghỉ việc có được trợ cấp thôi việc không?",
  "reference_date": "2026-09-09"
}
```

- `question`: bắt buộc, sau trim dài 1–2.000 ký tự.
- `reference_date`: tùy chọn; nếu `null` hoặc bỏ qua, resolver dùng ngày trong câu hỏi hoặc ngày hệ thống.

### Response `200`

```json
{
  "request_id": "req_01...",
  "status": "answered",
  "reference_date": "2026-09-09",
  "answer": {
    "conclusion": "... [C1]",
    "analysis": "... [C1]",
    "legal_basis": ["[C1] Điều 46 Bộ luật Lao động"],
    "notes": "Thông tin có tính chất hỗ trợ nghiên cứu, không thay thế tư vấn pháp lý."
  },
  "citations": [
    {
      "citation_id": "C1",
      "document_id": "vn_bll_45_2019_qh14",
      "chunk_id": "vn_bll_45_2019_qh14:article-46:clause-1__abc123",
      "document_number": "45/2019/QH14",
      "document_title": "Bộ luật Lao động",
      "article": "Điều 46",
      "clause": "Khoản 1",
      "point": null,
      "excerpt": "...",
      "effective_from": "2021-01-01",
      "effective_to": null,
      "source_url": "https://vbpl.vn/..."
    }
  ]
}
```

`status` là `answered` hoặc `insufficient_context`. Với `insufficient_context`, `citations` có thể rỗng hoặc chứa nguồn liên quan nhưng chưa đủ; `answer.conclusion` phải dùng thông báo abstention chuẩn. API MVP không trả numeric `confidence`.

## 4. `POST /api/search`

### Request

```json
{
  "query": "Khoản 1 Điều 46 trợ cấp thôi việc",
  "reference_date": "2026-09-09",
  "limit": 5
}
```

- `query`: bắt buộc, 1–2.000 ký tự.
- `limit`: tùy chọn, integer 1–20, mặc định 5.

### Response `200`

```json
{
  "request_id": "req_01...",
  "reference_date": "2026-09-09",
  "results": [
    {
      "rank": 1,
      "citation": {
        "citation_id": "C1",
        "document_id": "vn_bll_45_2019_qh14",
        "chunk_id": "vn_bll_45_2019_qh14:article-46:clause-1__abc123",
        "document_number": "45/2019/QH14",
        "document_title": "Bộ luật Lao động",
        "article": "Điều 46",
        "clause": "Khoản 1",
        "point": null,
        "excerpt": "...",
        "effective_from": "2021-01-01",
        "effective_to": null,
        "source_url": "https://vbpl.vn/..."
      },
      "score": 0.8123
    }
  ]
}
```

`score` chỉ dùng để sắp xếp trong cùng response, không được mô tả là xác suất đúng và không so sánh giữa các index/config version.

## 5. `GET /api/documents/{document_id}`

Trả metadata document, versions có trong corpus hiện tại, hierarchy và source URL. Endpoint không trả raw copyrighted artifact nếu quyền phân phối chưa được xác nhận.

Response `200`:

```json
{
  "request_id": "req_01...",
  "document": {
    "document_id": "vn_bll_45_2019_qh14",
    "document_number": "45/2019/QH14",
    "title": "Bộ luật Lao động",
    "document_type": "code",
    "issuer": "Quốc hội",
    "issued_date": "2019-11-20",
    "primary_source_url": "https://vbpl.vn/...",
    "versions": [
      {
        "version_id": "vn_bll_45_2019_qh14@2026-09-09:abc123",
        "retrieved_at": "2026-09-09T04:00:00Z"
      }
    ]
  }
}
```

`404 DOCUMENT_NOT_FOUND` khi ID không thuộc corpus version đang active.

## 6. `GET /api/health`

Response:

```json
{
  "status": "healthy",
  "checks": {
    "generator": "ok",
    "retriever": "ok",
    "corpus_index_match": "ok"
  },
  "versions": {
    "api": "v1",
    "corpus": "legal-corpus-v1",
    "index": "legal-index-v1",
    "model": "Qwen/Qwen3-4B@revision"
  }
}
```

`status`: `healthy`, `degraded` hoặc `unhealthy`. Endpoint không tiết lộ secret hoặc địa chỉ nội bộ.

## 7. HTTP status và error codes

| HTTP | Code | Khi dùng |
|---|---|---|
| 400 | `INVALID_REQUEST` | JSON hoặc content type không hợp lệ |
| 404 | `DOCUMENT_NOT_FOUND` | Không có document trong corpus active |
| 413 | `INPUT_TOO_LARGE` | Payload vượt giới hạn server |
| 422 | `VALIDATION_ERROR` | Field sai schema |
| 422 | `INVALID_REFERENCE_DATE` | Ngày sai hoặc mâu thuẫn |
| 429 | `RATE_LIMITED` | Chỉ bật khi cấu hình rate limit |
| 500 | `INTERNAL_ERROR` | Lỗi không dự kiến, không lộ chi tiết |
| 503 | `DEPENDENCY_UNAVAILABLE` | Model/index không sẵn sàng |
| 503 | `VERSION_MISMATCH` | Corpus và index không tương thích |

`insufficient_context` là kết quả nghiệp vụ hợp lệ và dùng HTTP 200, không phải lỗi server.

## 8. Compatibility

- Breaking change yêu cầu base path version mới, ví dụ `/api/v2`, trước khi có client production.
- Thêm optional response field không được làm client cũ lỗi.
- OpenAPI là executable contract và phải được kiểm tra bằng contract tests.

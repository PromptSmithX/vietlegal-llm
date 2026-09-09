# Data Specification — Legal Corpus v1

## 1. Phạm vi và nguồn

Corpus v1 chỉ nhận văn bản trong source manifest đã duyệt. Manifest bắt đầu bằng Bộ luật Lao động số 45/2019/QH14 và các nghị định, thông tư trực tiếp hướng dẫn.

Thứ tự ưu tiên nguồn:

1. [Cơ sở dữ liệu quốc gia về văn bản pháp luật](https://vbpl.vn/pages/portal.aspx) — nguồn chính cho nội dung, thuộc tính, hiệu lực và quan hệ văn bản.
2. [Cổng văn bản Chính phủ](https://vanban.chinhphu.vn/) — nguồn đối chiếu metadata và file chính thức.
3. Nguồn chính thức khác của Quốc hội hoặc cơ quan ban hành — chỉ dùng khi hai nguồn trên thiếu artifact.

Nguồn thương mại, blog, diễn đàn và bài bình luận không được đưa vào legal corpus. Dataset nghiên cứu có thể dùng cho training/evaluation nếu có license và provenance riêng, nhưng không được trở thành căn cứ trả lời.

## 2. Source manifest

Manifest dùng YAML hoặc JSON, được version cùng repository. Mỗi entry bắt buộc có:

```yaml
document_number: "45/2019/QH14"
title: "Bộ luật Lao động"
scope_reason: "Văn bản gốc của corpus luật lao động v1"
primary_url: "https://vbpl.vn/..."
crosscheck_urls:
  - "https://vanban.chinhphu.vn/..."
expected_document_type: "Bộ luật"
enabled: true
```

Crawler không tự mở rộng corpus từ link liên quan. Văn bản mới chỉ được ingest sau khi thêm vào manifest và ghi lý do phạm vi.

## 3. Raw artifact và provenance

Mỗi lần tải phải lưu:

- raw HTML và/hoặc PDF/DOC gốc;
- URL cuối cùng sau redirect;
- `retrieved_at` theo UTC;
- HTTP metadata cần thiết;
- SHA-256 của từng artifact;
- crawler version và parser version;
- source manifest version.

Raw artifact là immutable. Nếu nội dung tại cùng URL thay đổi, tạo artifact mới với checksum và thời điểm mới; không ghi đè bản cũ.

## 4. Canonical types

Ngày dùng ISO 8601 `YYYY-MM-DD`; timestamp dùng UTC ISO 8601. Trường chưa biết dùng `null`, không dùng chuỗi rỗng hoặc giá trị suy đoán.

### 4.1 `LegalDocument`

Đại diện danh tính ổn định của một văn bản pháp luật.

```json
{
  "document_id": "vn_bll_45_2019_qh14",
  "document_number": "45/2019/QH14",
  "title": "Bộ luật Lao động",
  "document_type": "code",
  "issuer": "Quốc hội",
  "issued_date": "2019-11-20",
  "jurisdiction": "VN",
  "primary_source_url": "https://vbpl.vn/..."
}
```

`document_type` thuộc một trong: `constitution`, `code`, `law`, `resolution`, `decree`, `decision`, `circular`, `joint_circular`, `consolidated_text`, `other`.

### 4.2 `DocumentVersion`

Đại diện một snapshot có thể tái lập của văn bản.

```json
{
  "version_id": "vn_bll_45_2019_qh14@2026-09-09:sha256-prefix",
  "document_id": "vn_bll_45_2019_qh14",
  "retrieved_at": "2026-09-09T04:00:00Z",
  "content_sha256": "...",
  "parser_version": "legal-parser-0.1.0",
  "manifest_version": "labor-sources-v1",
  "source_artifacts": ["raw/...pdf", "raw/...html"],
  "relations": []
}
```

`relations` chứa các object `{type, target_document_id, source_url}` với `type`: `amends`, `amended_by`, `replaces`, `replaced_by`, `consolidates`, `guided_by`, `guides`.

### 4.3 `LegalProvision`

Đơn vị cấu trúc nhỏ nhất được parser xác định chắc chắn.

```json
{
  "provision_id": "vn_bll_45_2019_qh14:article-46:clause-1",
  "version_id": "vn_bll_45_2019_qh14@2026-09-09:sha256-prefix",
  "chapter": "Chương III",
  "section": null,
  "article": "Điều 46",
  "clause": "Khoản 1",
  "point": null,
  "heading": "Trợ cấp thôi việc",
  "text": "...",
  "effective_from": "2021-01-01",
  "effective_to": null,
  "validity_status": "effective",
  "validity_source_url": "https://vbpl.vn/..."
}
```

`validity_status` thuộc một trong: `not_yet_effective`, `effective`, `partially_effective`, `expired`, `unknown`.

`effective_from` là ngày đầu tiên có hiệu lực. `effective_to`, nếu có, là ngày đầu tiên không còn hiệu lực. Khi nguồn chỉ cho biết văn bản hết hiệu lực một phần nhưng chưa đủ dữ liệu xác định provision bị tác động, provision phải mang `validity_status: unknown` hoặc `partially_effective`; không được tự suy ra còn hiệu lực.

### 4.4 `LegalChunk`

Đơn vị đưa vào retrieval.

```json
{
  "chunk_id": "vn_bll_45_2019_qh14:article-46:clause-1__sha256-prefix",
  "document_id": "vn_bll_45_2019_qh14",
  "version_id": "vn_bll_45_2019_qh14@2026-09-09:sha256-prefix",
  "provision_ids": ["vn_bll_45_2019_qh14:article-46:clause-1"],
  "display_header": "Bộ luật Lao động | Điều 46 | Khoản 1",
  "text": "...",
  "effective_from": "2021-01-01",
  "effective_to": null,
  "validity_status": "effective",
  "source_url": "https://vbpl.vn/...",
  "content_sha256": "..."
}
```

## 5. ID và chuẩn hóa

- `document_id` sinh từ jurisdiction, loại và số văn bản đã canonicalize; không phụ thuộc URL hoặc tiêu đề.
- `version_id` gồm `document_id`, ngày snapshot và prefix checksum.
- `provision_id` gồm `document_id` và đường dẫn hierarchy canonical.
- `chunk_id` gồm phạm vi provision và prefix checksum nội dung.
- Unicode chuẩn NFC; giữ nguyên dấu tiếng Việt trong text hiển thị.
- Số văn bản được chuẩn hóa chữ hoa và bỏ khoảng trắng thừa, không thay đổi dấu `/` hoặc `-` có nghĩa.
- Nội dung giống checksum trong cùng document/version được deduplicate; khác checksum phải tạo version mới.

## 6. Parsing và chunking

Hierarchy chuẩn:

```text
Văn bản → Chương → Mục → Điều → Khoản → Điểm
```

Quy tắc:

- Một Điều không quá 1.200 model tokens tạo một chunk.
- Điều dài hơn được tách tại ranh giới Khoản; không tách giữa một Khoản hoặc Điểm.
- Nếu một Khoản riêng vượt 1.200 tokens, giữ toàn bộ Khoản thành một chunk và gắn cờ `oversized`; không cắt mù.
- Mỗi chunk lặp lại tên văn bản, số văn bản, hierarchy và thông tin hiệu lực trong `display_header`/metadata.
- Không dùng overlap nội dung giữa hai chunk pháp lý; header có thể lặp lại.
- Footnote và chú thích sửa đổi phải được tách khỏi normative text nhưng liên kết bằng metadata.

## 7. Temporal applicability

Một provision chắc chắn áp dụng tại `reference_date` khi:

```text
effective_from <= reference_date
AND (effective_to IS NULL OR reference_date < effective_to)
AND validity_status = effective
```

`partially_effective` và `unknown` không được tự động coi là hợp lệ. Chúng có thể xuất hiện trong search diagnostics nhưng không được dùng để tạo kết luận `answered` nếu chưa có metadata cấp provision xác nhận.

## 8. Dataset build và versioning

Tên version:

```text
legal-corpus-v1
legal-corpus-v1.1
legal-eval-v1
legal-sft-v1
```

Mỗi release corpus phải kèm:

- manifest và checksum toàn bộ artifact;
- số document/version/provision/chunk;
- schema version và parser version;
- danh sách lỗi, field `unknown` và văn bản bị loại;
- diff so với release trước;
- commit hash sinh dataset.

Không overwrite release cũ. Index phải tham chiếu chính xác corpus version và embedding model revision.

## 9. Data quality gate

- 100% record pass JSON Schema/Pydantic validation.
- 100% chunk có `document_id`, `version_id`, `chunk_id`, hierarchy, validity và provenance.
- Không có duplicate stable ID trong cùng release.
- Kiểm tra kỹ thuật ngẫu nhiên tối thiểu 50 Điều/Khoản; ≥ 98% đúng hierarchy và text.
- Mọi trường hợp hiệu lực không xác định được ghi rõ; không suy đoán để đạt coverage.


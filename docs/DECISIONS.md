# Architecture Decision Log

Tài liệu này ghi các quyết định đã khóa cho MVP. Thay đổi quyết định phải bổ sung entry mới; không xóa lịch sử.

## ADR-001 — MVP tập trung luật lao động

**Status:** Accepted

**Decision:** Corpus v1 gồm Bộ luật Lao động 2019 và các văn bản trực tiếp hướng dẫn.

**Rationale:** Phạm vi đủ hẹp để xây gold benchmark và kiểm tra hiệu lực, nhưng đủ rộng cho tình huống thực tế.

**Revisit when:** MVP đạt gate và có nguồn lực/chuyên gia để mở rộng lĩnh vực.

## ADR-002 — Chỉ nguồn chính thức làm căn cứ

**Status:** Accepted

**Decision:** `vbpl.vn` là nguồn chính; cổng văn bản Chính phủ và nguồn của cơ quan ban hành dùng đối chiếu.

**Consequence:** Bài viết, blog và dataset nghiên cứu không xuất hiện như legal citation.

## ADR-003 — Hiệu lực ở cấp provision/chunk

**Status:** Accepted

**Decision:** Lưu `effective_from`, `effective_to` và `validity_status` ở cấp provision/chunk; không suy ra toàn bộ Điều còn hiệu lực từ trạng thái chung của văn bản.

**Consequence:** Record `partially_effective` hoặc `unknown` không dùng để kết luận cho đến khi được xác minh.

## ADR-004 — Retrieval order và Top K

**Status:** Accepted

**Decision:** BM25 Top 100 + Dense Top 100 → temporal filter → RRF Top 30 (`k=60`) → reranker Top 5.

**Consequence:** Cấu hình được version; threshold chọn trên validation set.

## ADR-005 — API MVP stateless

**Status:** Accepted

**Decision:** Không tài khoản, không lưu hội thoại, không streaming và không authentication trong MVP.

**Consequence:** MVP chỉ triển khai trong môi trường demo/kiểm soát; production phải thêm identity và policy phù hợp.

## ADR-006 — Không phát hành numeric confidence

**Status:** Accepted

**Decision:** `/api/chat` trả `answered` hoặc `insufficient_context`; không trả xác suất/confidence chưa calibrated.

**Consequence:** Search score chỉ có ý nghĩa xếp hạng trong một response.

## ADR-007 — Backend sở hữu citation metadata

**Status:** Accepted

**Decision:** Model chỉ phát citation ID từ context. Backend ánh xạ document, hierarchy và URL rồi validate trước response.

**Consequence:** URL hoặc Điều/Khoản do model tự viết không được tin cậy.

## ADR-008 — Fine-tuning sau RAG baseline

**Status:** Accepted

**Decision:** Chỉ SFT khi corpus, retrieval, RAG và evaluation đã ổn định, và error analysis chứng minh lỗi thuộc generator.

**Consequence:** Không dùng training để che lỗi data/retrieval hoặc ghi nhớ luật.

## ADR-009 — Môi trường phát triển và triển khai

**Status:** Accepted

**Decision:** Local cho development, Colab/Kaggle cho GPU training và Docker Linux cho deployment.

**Consequence:** Code/config phải portable và không giả định unified VRAM nhiều GPU.

## ADR-010 — Đánh giá hiện chỉ có giá trị kỹ thuật

**Status:** Accepted

**Decision:** Khi chưa có chuyên gia pháp lý, benchmark đo retrieval/grounding và không được quảng bá là chứng nhận đúng pháp luật.

**Revisit when:** Có reviewer pháp lý phê duyệt gold labels, rubric và representative outputs.

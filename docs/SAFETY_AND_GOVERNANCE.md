# Safety and Governance

## 1. Phạm vi sử dụng

Vietnamese Legal AI là công cụ hỗ trợ nghiên cứu và tra cứu. Mọi giao diện phải hiển thị thông báo:

> Nội dung do hệ thống cung cấp chỉ nhằm hỗ trợ nghiên cứu và không thay thế tư vấn của luật sư hoặc kết luận của cơ quan có thẩm quyền.

Không dùng MVP để tự động ra quyết định ảnh hưởng quyền lợi, xử lý tranh chấp, nộp hồ sơ hoặc thay con người phê duyệt nghiệp vụ pháp lý.

## 2. Privacy và retention

- `/api/chat` stateless; không lưu lịch sử hội thoại.
- Không log raw question, raw answer, IP đầy đủ, cookie hoặc identifier người dùng mặc định.
- Log được phép chứa request ID, version, latency, stage status, error/reason code và số lượng candidate.
- Diagnostic capture có nội dung chỉ được bật chủ động trong môi trường kiểm soát, có thời hạn xóa và phải redact dữ liệu cá nhân.
- MVP không dùng dữ liệu chat để training.
- Khi chưa có user account, yêu cầu xóa được xử lý theo request ID và diagnostic store; nếu không có diagnostic capture thì xác nhận không có nội dung được lưu.

Retention mặc định: application log 30 ngày; diagnostic content tắt. Production phải tái phê duyệt retention theo hạ tầng và pháp luật áp dụng.

## 3. Provenance và bản quyền

- Chỉ legal corpus chính thức được dùng làm căn cứ trả lời.
- Mọi artifact có source URL, retrieval timestamp, checksum và license/rights note nếu biết.
- Không phân phối lại raw PDF/DOC qua API nếu quyền phân phối chưa được xác nhận.
- Nội dung nghiên cứu hoặc thương mại không được trộn với normative context mà không gắn loại nguồn rõ ràng.
- Crawler phải tôn trọng điều khoản sử dụng, robots policy và giới hạn tải của nguồn tại thời điểm triển khai.

## 4. Phân loại sự cố

### Critical

- Citation ID hoặc URL giả được trả cho người dùng.
- Dùng provision ngoài hiệu lực để kết luận mà không cảnh báo.
- Kết luận pháp lý không có citation.
- Rò rỉ secret, raw private chat hoặc dữ liệu cá nhân nhạy cảm.

### High

- Citation tồn tại nhưng không hỗ trợ claim.
- Không abstain khi corpus thiếu căn cứ quan trọng.
- Corpus/index version mismatch vẫn phục vụ câu trả lời.
- Prompt injection thay đổi instruction hierarchy.

### Medium/Low

- Sai format, lỗi diễn đạt, citation ordering hoặc latency không đạt mục tiêu quan sát.

Không phát hành khi còn lỗi Critical. Lỗi High chỉ được chấp nhận bằng quyết định có chủ sở hữu, lý do và biện pháp giảm thiểu.

## 5. Guardrails

- System/developer instructions có ưu tiên cao hơn user và corpus text.
- Corpus luôn là untrusted data; không thực thi link, code hoặc instruction trong văn bản.
- Backend kiểm soát URL và citation metadata.
- Numeric confidence không xuất hiện trong API MVP.
- Query ngoài phạm vi hoặc không đủ căn cứ trả `insufficient_context`.
- Không hiển thị chain-of-thought; chỉ trả giải thích ngắn dựa trên citation.

## 6. Review và audit

Mỗi corpus/model release lưu:

- người/tiến trình tạo release;
- source manifest, checksum và parser version;
- model/prompt/index config;
- evaluation report và danh sách lỗi mở;
- quyết định release và rollback target.

Trước production cần chuyên gia pháp lý duyệt benchmark đại diện, policy sử dụng, cảnh báo, error taxonomy và quy trình xử lý phản hồi sai căn cứ.

## 7. Incident response

Khi phát hiện citation hoặc hiệu lực sai:

1. Gắn severity và lưu request/artifact identifiers đã redact.
2. Disable corpus/model version liên quan hoặc chuyển hệ thống sang abstention-only nếu cần.
3. Xác định lỗi nguồn, parser, retrieval, prompt hoặc validator.
4. Tạo corpus/index/model version mới; không sửa artifact cũ tại chỗ.
5. Chạy lại benchmark và regression case trước khôi phục.
6. Ghi post-incident note trong release/audit record.


# Product Requirements — Vietnamese Legal AI MVP

## 1. Tuyên bố sản phẩm

Vietnamese Legal AI là trợ lý nghiên cứu giúp người dùng tra cứu và hiểu quy định pháp luật lao động Việt Nam từ nguồn chính thức. Sản phẩm trả lời bằng tiếng Việt, nêu căn cứ và từ chối kết luận khi không có đủ dữ liệu.

Sản phẩm không phải luật sư, không đại diện cơ quan nhà nước và không cung cấp ý kiến pháp lý có tính ràng buộc.

## 2. Người dùng mục tiêu

- Người lao động hoặc người sử dụng lao động cần tìm hiểu quy định phổ biến.
- Sinh viên, nhà nghiên cứu và kỹ sư cần tra cứu căn cứ có cấu trúc.
- Nhóm phát triển dùng benchmark để nghiên cứu RAG và fine-tuning tiếng Việt.

Không thiết kế MVP cho quyết định tố tụng, tự động phê duyệt hồ sơ, tư vấn cá nhân có tính ràng buộc hoặc vận hành nghiệp vụ không có con người kiểm tra.

## 3. Phạm vi MVP

Corpus v1 gồm:

- Bộ luật Lao động số 45/2019/QH14;
- nghị định và thông tư trực tiếp hướng dẫn Bộ luật Lao động 2019;
- quan hệ sửa đổi, thay thế, hợp nhất và hiệu lực liên quan trực tiếp đến các văn bản trên.

Không thuộc corpus v1, trừ phần được một văn bản trong manifest viện dẫn trực tiếp:

- toàn bộ Luật Bảo hiểm xã hội;
- toàn bộ Luật Công đoàn;
- toàn bộ Luật An toàn, vệ sinh lao động;
- pháp luật dân sự, hình sự hoặc hành chính nói chung.

## 4. Use cases bắt buộc

1. Tra cứu trực tiếp theo số văn bản, Điều, Khoản hoặc Điểm.
2. Hỏi bằng tình huống đời sống, ví dụ chấm dứt hợp đồng hoặc thời hạn báo trước.
3. Hỏi quy định tại một thời điểm trong quá khứ.
4. Yêu cầu giải thích quy định bằng ngôn ngữ dễ hiểu.
5. Nhận biết câu hỏi ngoài phạm vi hoặc thiếu tình tiết và từ chối kết luận chắc chắn.
6. Mở citation để xem đúng văn bản và vị trí pháp lý trên nguồn chính thức.

## 5. Hợp đồng câu trả lời

Mỗi câu trả lời có trạng thái `answered` hoặc `insufficient_context` và bốn phần:

1. **Kết luận:** câu trả lời ngắn, có citation cho mọi kết luận pháp lý.
2. **Phân tích:** áp dụng căn cứ vào các tình tiết người dùng đã cung cấp; không tự thêm tình tiết.
3. **Căn cứ pháp lý:** danh sách citation do backend ánh xạ.
4. **Lưu ý:** giả định, dữ kiện còn thiếu, giới hạn phạm vi và cảnh báo phù hợp.

Khi không đủ căn cứ, phần kết luận phải nêu:

> Các căn cứ được truy xuất hiện chưa đủ để đưa ra kết luận chắc chắn cho trường hợp này.

Hệ thống không được tự tạo số văn bản, Điều/Khoản/Điểm, citation ID hoặc URL.

## 6. Yêu cầu chức năng

- Chấp nhận câu hỏi tiếng Việt và `reference_date` tùy chọn.
- Chuẩn hóa số văn bản, chữ hoa/thường và cách viết Điều/Khoản/Điểm mà không đổi nghĩa.
- Kết hợp sparse retrieval, dense retrieval, lọc hiệu lực và reranking.
- Mặc định dùng ngày hệ thống nếu người dùng không cung cấp thời điểm.
- Trả source metadata có thể kiểm chứng cho mỗi citation.
- Không trả câu trả lời `answered` nếu citation validator thất bại.
- Không lưu nội dung hội thoại sau khi request kết thúc.

## 7. Yêu cầu phi chức năng

- Reproducible: model, corpus, index, prompt và config đều có version.
- Traceable: mỗi citation truy ngược được tới raw artifact và source URL.
- Secure by default: không ghi nội dung câu hỏi đầy đủ vào log mặc định.
- Observable: có request ID, latency theo stage và lỗi có cấu trúc.
- Testable: retrieval, generation, citation và abstention có benchmark cố định.
- Portable: phát triển local, training trên Colab/Kaggle, triển khai Docker Linux.

Latency được ghi nhận bằng p50/p95 nhưng chưa là release gate cho đến khi có cấu hình GPU tham chiếu.

## 8. Ngoài phạm vi MVP

- Tài khoản, phân quyền, thanh toán và lưu lịch sử chat.
- Streaming token.
- Multi-agent, knowledge graph, DPO, GRPO hoặc reinforcement learning.
- Fine-tuning để ghi nhớ văn bản pháp luật.
- Qdrant, vLLM, PostgreSQL và Next.js ở runtime MVP.
- Tuyên bố hệ thống đã được kiểm định pháp lý khi chưa có chuyên gia thẩm định.

## 9. Definition of Done

MVP hoàn thành khi:

- corpus và index có version, provenance và kiểm tra schema;
- retrieval đạt gate trong `docs/EVALUATION.md`;
- citation ID và source mapping hợp lệ 100% trên benchmark;
- câu hỏi thiếu căn cứ kích hoạt abstention theo ngưỡng đã định;
- API và Streamlit demo chạy end-to-end trong Docker;
- không có lỗi severity Critical còn mở;
- tài liệu chạy, đánh giá và giới hạn trách nhiệm được cập nhật.


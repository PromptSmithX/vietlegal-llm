# Development and Operations

## 1. Môi trường mục tiêu

- Development và ingestion: máy local, Python chạy được trên Windows và Linux.
- Baseline/fine-tuning: Colab hoặc Kaggle GPU.
- MVP deployment: Docker trên Linux, một generator instance và file-based FAISS artifacts.
- Production target: Linux GPU, Qdrant, vLLM; PostgreSQL chỉ khi metadata cần transaction/query phức tạp.

Không giả định nhiều GPU tạo thành unified VRAM.

## 2. Repository layout mục tiêu

```text
api/                 FastAPI entrypoint và schemas
frontend/            Streamlit MVP
src/ingestion/       crawler, parser, chunker
src/retrieval/       BM25, dense, RRF, reranker
src/rag/             query, context, prompt, pipeline, validator
src/model/           generator abstraction
src/evaluation/      metrics và runners
training/            dataset prep, train, evaluate, config
data/                manifest; raw/processed artifacts bị git-ignore
tests/               unit, integration, contract, e2e fixtures
docker/              image/compose assets
docs/                executable specifications
```

## 3. Dependency và configuration

- Dùng `pyproject.toml` làm nguồn metadata/dependency chính và một lockfile được commit.
- Pin model revision và major/minor version của Transformers, TRL, PEFT, Datasets, PyTorch, sentence-transformers và FAISS.
- Config phân lớp: defaults có version → file môi trường → environment variables cho secret/override.
- Không hard-code path, token, URL credential hoặc GPU ID.
- Cung cấp `.env.example` chỉ chứa tên biến và giá trị giả.
- Mỗi run materialize resolved config vào artifact directory.

Biến cấu hình tối thiểu:

```text
APP_ENV
LOG_LEVEL
TIMEZONE=Asia/Ho_Chi_Minh
CORPUS_VERSION
INDEX_VERSION
GENERATOR_MODEL
GENERATOR_REVISION
EMBEDDING_MODEL
EMBEDDING_REVISION
RERANKER_MODEL
RERANKER_REVISION
ARTIFACT_ROOT
```

## 4. Artifact management

- Raw corpus, processed corpus, index, checkpoints và result outputs không commit vào Git.
- Commit manifest, schema, config, checksums và small deterministic fixtures.
- Artifact directory chứa `metadata.json` với type, version, created time, source versions, config hash và commit hash.
- Loader phải fail closed nếu corpus/index/model metadata không tương thích.

## 5. Test strategy

### Unit

- ID normalization, date resolution và temporal predicate.
- Legal hierarchy parser và chunk boundary.
- RRF calculation, deduplication và rank stability.
- Citation extraction, mapping và forbidden URL detection.
- Request validation và error serialization.

### Integration

- Manifest → raw fixture → provision → chunk → index.
- Query → retrieval → temporal filter → reranker → context.
- Generator stub → output parser → citation validator → API response.
- Corpus/index version mismatch và dependency timeout.

### Contract

- OpenAPI phù hợp `docs/API_SPEC.md`.
- Request/response examples pass schema validation.
- Unknown request fields và invalid date trả đúng 422/error code.

### End-to-end

- Chạy các acceptance scenarios trong `docs/EVALUATION.md` bằng deterministic fixture/stub và một GPU smoke suite riêng.

## 6. CI

Mọi pull request chạy:

1. Markdown link/style checks.
2. Lint và format check không rewrite.
3. Static type-check.
4. Unit, schema và contract tests.
5. Integration tests không cần tải model lớn.
6. Secret scan và dependency vulnerability report.

GPU/model tests chạy theo lịch hoặc manual workflow, lưu artifact và không chặn thay đổi docs thuần túy nếu CPU suite đạt.

## 7. Logging và monitoring

Structured log gồm request ID, stage, status, reason code, latency, version và candidate count. Raw user/model text tắt mặc định.

Metrics tối thiểu:

- request/error/abstention rate;
- p50/p95 latency theo stage;
- retrieval candidate counts;
- citation validation failure;
- model timeout/OOM;
- corpus-index mismatch;
- active corpus/index/model versions.

## 8. Docker và release

- Multi-stage image, non-root runtime, read-only application code.
- Model/corpus/index mount hoặc tải bằng checksum; không bake secret vào image.
- `/api/health` kiểm tra dependency và version compatibility.
- Release tag liên kết Git commit, image digest, corpus/index/model/prompt versions và evaluation report.

## 9. Production migration

1. FAISS → Qdrant nhưng giữ `chunk_id` và retrieval contract.
2. Transformers generator → vLLM qua adapter interface tương thích.
3. File metadata → PostgreSQL chỉ khi cần update/query đồng thời.
4. Streamlit → Next.js, sau đó thêm authentication/authorization.
5. Thêm rate limit, queue/backpressure, monitoring, backup và rollback.

Mỗi migration phải chạy cùng benchmark và so sánh parity trước chuyển traffic.


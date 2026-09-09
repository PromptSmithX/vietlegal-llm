from __future__ import annotations


def test_all_phase_boundaries_are_importable() -> None:
    import vietlegal.evaluation  # noqa: F401
    import vietlegal.ingestion  # noqa: F401
    import vietlegal.model  # noqa: F401
    import vietlegal.rag  # noqa: F401
    import vietlegal.retrieval  # noqa: F401

"""Tests for process-local and persistent rate limiting."""

from __future__ import annotations

from nanobot.access.rate_limit import RateLimitStore


def test_short_window_blocks() -> None:
    store = RateLimitStore()
    for _ in range(5):
        allowed, _ = store.check("local")
        assert allowed
        store.record("local")
    allowed, retry = store.check("local")
    assert not allowed
    assert retry > 0


def test_global_floor_blocks() -> None:
    store = RateLimitStore()
    # Exhaust the global budget across multiple sources
    for i in range(60):
        store.record(f"src-{i}")
    allowed, retry = store.check("src-new")
    assert not allowed
    assert retry > 0


def test_independent_sources() -> None:
    store = RateLimitStore()
    for _ in range(5):
        store.record("a")
    allowed, _ = store.check("b")
    assert allowed


def test_reset() -> None:
    store = RateLimitStore()
    for _ in range(3):
        store.record("a")
    store.reset()
    allowed, _ = store.check("a")
    assert allowed


def test_persistent_attempt_budget_survives_store_recreation(tmp_path) -> None:
    path = tmp_path / "auth" / "rate-limits.json"
    source = "192.0.2.17"
    for _ in range(5):
        allowed, _ = RateLimitStore(path=path).check_and_record(source)
        assert allowed

    restarted = RateLimitStore(path=path)
    allowed, retry = restarted.check_and_record(source)
    assert not allowed
    assert retry > 0
    payload = path.read_text()
    assert source not in payload


def test_success_can_clear_persistent_source_history(tmp_path) -> None:
    path = tmp_path / "auth" / "rate-limits.json"
    store = RateLimitStore(path=path)
    for _ in range(5):
        assert store.check_and_record("local")[0]
    store.clear_source("local")
    assert RateLimitStore(path=path).check_and_record("local")[0]

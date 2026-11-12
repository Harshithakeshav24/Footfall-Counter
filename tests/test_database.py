from app import config, database


def test_save_and_read_history(tmp_path, monkeypatch):
    monkeypatch.setattr(config, "DB_PATH", str(tmp_path / "test.db"))
    database.init_db()

    database.save_event("in", 1, 0, 1)
    database.save_event("out", 1, 1, 2)

    history = database.get_history(limit=10)
    assert len(history) == 2
    assert history[0]["direction"] == "out"  # newest first
    assert history[0]["total_count"] == 2
    assert "timestamp" in history[0]

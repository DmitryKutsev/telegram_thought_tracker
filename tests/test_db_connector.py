from datetime import datetime, timedelta
from unittest.mock import patch

import pytest

from db_connector import DatabaseConnector, Thought


@pytest.fixture
def db(tmp_path, monkeypatch):
    db_file = str(tmp_path / "test.db")
    monkeypatch.setattr("db_connector.DATABASE_FILE", db_file)
    monkeypatch.setattr("db_connector.MAX_DB_SIZE", 100 * 1024 * 1024)
    return DatabaseConnector()


class TestAddThought:
    def test_stores_all_fields(self, db):
        db.add_thought(123, "alice", "I had a strange dream", "dream")

        session = db.Session()
        thought = session.query(Thought).one()
        session.close()

        assert thought.user_tg_id == 123
        assert thought.username == "alice"
        assert thought.text == "I had a strange dream"
        assert thought.type == "dream"

    @pytest.mark.parametrize("thought_type", ["dream", "thought", "plans"])
    def test_all_types_accepted(self, db, thought_type):
        db.add_thought(1, "user", "content", thought_type)

        session = db.Session()
        thought = session.query(Thought).one()
        session.close()

        assert thought.type == thought_type

    def test_datetime_set_close_to_now(self, db):
        before = datetime.now()
        db.add_thought(1, "user", "text", "thought")
        after = datetime.now()

        session = db.Session()
        thought = session.query(Thought).one()
        session.close()

        assert before <= thought.datetime <= after


class TestDeleteOldestEntries:
    def test_removes_oldest_records_in_order(self, db):
        session = db.Session()
        for i in range(5):
            session.add(
                Thought(
                    user_tg_id=1,
                    username="user",
                    text=f"thought {i}",
                    type="thought",
                    datetime=datetime.now() - timedelta(hours=5 - i),
                )
            )
        session.commit()
        session.close()

        db._delete_oldest_entries(3)

        session = db.Session()
        remaining = session.query(Thought).order_by(Thought.datetime).all()
        session.close()

        assert len(remaining) == 2
        assert remaining[0].text == "thought 3"
        assert remaining[1].text == "thought 4"


class TestCheckDbSize:
    def test_triggers_cleanup_when_over_limit(self, db, monkeypatch):
        monkeypatch.setattr("db_connector.MAX_DB_SIZE", 1)

        with patch.object(db, "_delete_oldest_entries") as mock_delete:
            db._check_db_size()

        mock_delete.assert_called_once_with(1000)

    def test_no_cleanup_when_under_limit(self, db):
        with patch.object(db, "_delete_oldest_entries") as mock_delete:
            db._check_db_size()

        mock_delete.assert_not_called()


class TestExecuteCustomQuery:
    def test_returns_matching_records(self, db):
        db.add_thought(42, "alice", "flying dream", "dream")

        result = db.execute_custom_query(
            "SELECT * FROM thoughts WHERE username = 'alice'", 42, "alice"
        )

        assert result is not None
        combined = "".join(result)
        assert "flying dream" in combined

    def test_blocks_mismatched_username(self, db):
        result = db.execute_custom_query(
            "SELECT * FROM thoughts WHERE username = 'eve'", 42, "alice"
        )

        assert result is None

    def test_empty_result_returns_not_found_message(self, db):
        result = db.execute_custom_query(
            "SELECT * FROM thoughts WHERE username = 'nobody'", 1, "nobody"
        )

        assert result is not None
        assert result[0] == "No information found for the query"

    def test_no_username_skips_security_check(self, db):
        db.add_thought(42, "alice", "my thought", "thought")

        result = db.execute_custom_query("SELECT * FROM thoughts", 42, username=None)

        assert result is not None

    def test_double_quoted_username_passes(self, db):
        db.add_thought(42, "alice", "dreaming of flight", "dream")

        result = db.execute_custom_query(
            'SELECT * FROM thoughts WHERE username = "alice"', 42, "alice"
        )

        assert result is not None
        assert any("dreaming of flight" in r for r in result)

    def test_row_level_filter_excludes_other_users(self, db):
        db.add_thought(42, "alice", "alice's secret dream", "dream")
        db.add_thought(99, "alice", "impostor's entry", "thought")

        result = db.execute_custom_query(
            "SELECT * FROM thoughts WHERE username = 'alice'", 42, "alice"
        )

        assert result is not None
        combined = "".join(result)
        assert "alice's secret dream" in combined
        assert "impostor's entry" not in combined
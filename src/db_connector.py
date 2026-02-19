import os
import re
from datetime import datetime

from loguru import logger
from sqlalchemy import Column, DateTime, Enum, Integer, Text, create_engine, text
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, declarative_base, sessionmaker

from config import settings

DATABASE_FILE = settings.DATABASE_FILE
MAX_DB_SIZE = settings.MAX_DB_SIZE

Base = declarative_base()


class Thought(Base):
    __tablename__ = "thoughts"

    id = Column(Integer, primary_key=True)
    datetime = Column(DateTime, default=datetime.utcnow)

    user_tg_id = Column(Integer, nullable=False)
    username = Column(Text)
    text = Column(Text)
    type = Column(Enum("dream", "thought", "plans"))


class DatabaseConnector:
    def __init__(self) -> None:

        if not os.path.exists(DATABASE_FILE):
            logger.info(
                f"Database file '{DATABASE_FILE}' not found. Creating a new one."
            )

            open(DATABASE_FILE, "w").close()

        self.engine: Engine = create_engine(f"sqlite:///{DATABASE_FILE}")
        Base.metadata.create_all(self.engine)  # Create tables if they don't exist
        self.Session: sessionmaker[Session] = sessionmaker(bind=self.engine)

    def add_thought(self, user_tg_id: int, username: str | None, text: str | None, type: str) -> None:
        session: Session = self.Session()

        try:
            new_thought = Thought(
                user_tg_id=user_tg_id, username=username, text=text, type=type
            )

            session.add(new_thought)
            session.commit()
            self._check_db_size()

        except Exception as e:
            session.rollback()
            logger.error(f"Error adding thought: {e}")

        finally:
            session.close()

    def _check_db_size(self) -> None:
        file_size = os.path.getsize(DATABASE_FILE)

        if file_size > MAX_DB_SIZE:
            logger.warning("Database size exceeded limit. Cleaning up oldest entries.")
            self._delete_oldest_entries(1000)

    def _delete_oldest_entries(self, num_to_delete: int) -> None:
        session: Session = self.Session()

        try:
            oldest_entries = (
                session.query(Thought)
                .order_by(Thought.datetime)
                .limit(num_to_delete)
                .all()
            )

            for entry in oldest_entries:
                session.delete(entry)

            session.commit()
            logger.info(f"Deleted {num_to_delete} oldest entries.")

        except Exception as e:
            session.rollback()
            logger.error(f"Error deleting oldest entries: {e}")

        finally:
            session.close()

    def execute_custom_query(
        self, query: str, user_tg_id: int, username: str | None = None
    ) -> list[str] | None:
        # Security check: validate that username in WHERE clause matches Telegram username
        if username:
            # Match pattern: username = 'telegram_username' (with single or double quotes, with/without spaces)
            # Directly check if the value matches the Telegram username
            pattern = rf"username\s*=\s*['\"]{re.escape(username)}['\"]"
            match = re.search(pattern, query.lower())

            if not match:
                logger.error(
                    f"Security validation failed: username '{username}' not found in WHERE clause for user {user_tg_id}. Query: {query}"
                )
                return None

        session = self.Session()
        try:
            result = session.execute(text(query))
            rows = result.fetchall()

            if not rows:
                logger.info(f"Empty result from database query. Query: {query}")
                my_response = ["No information found for the query"]
            else:
                my_response = ["<b>Here is your data:</b>\n"]

                for thought in rows:
                    # Additional safety check: verify each result belongs to the user
                    if (
                        hasattr(thought, "user_tg_id")
                        and thought.user_tg_id != user_tg_id
                    ):
                        logger.warning(
                            f"Query returned data for different user. Expected {user_tg_id}, got {thought.user_tg_id}"
                        )
                        continue

                    resp_string = (
                        f"<b>User:</b> {thought.username}\n"
                        f"<b>Date:</b> {thought.datetime}\n"
                        f"<b>Type:</b> {thought.type}\n"
                        f"<b>Text:</b> {thought.text}\n\n"
                    )
                    my_response.append(resp_string)

            return my_response

        except Exception as e:
            session.rollback()
            logger.error(f"Error executing custom query: {e}")
            return None
        finally:
            session.close()

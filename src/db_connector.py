import os
from datetime import datetime

from loguru import logger
from sqlalchemy import Column, DateTime, Enum, Integer, Text, create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

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
    def __init__(self):
        # Check if the database file exists, create if not
        if not os.path.exists(DATABASE_FILE):
            logger.info(
                f"Database file '{DATABASE_FILE}' not found. Creating a new one."
            )
            # Create an empty file to avoid sqlalchemy errors
            open(DATABASE_FILE, "w").close()

        self.engine = create_engine(f"sqlite:///{DATABASE_FILE}")
        Base.metadata.create_all(self.engine)  # Create tables if they don't exist
        self.Session = sessionmaker(bind=self.engine)

    def add_thought(self, user_tg_id, username, text, type):
        session = self.Session()
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

    def _check_db_size(self):
        file_size = os.path.getsize(DATABASE_FILE)
        if file_size > MAX_DB_SIZE:
            logger.warning("Database size exceeded limit. Cleaning up oldest entries.")
            self._delete_oldest_entries(1000)

    def _delete_oldest_entries(self, num_to_delete):
        session = self.Session()
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

    def get_last_thoughts(self, user_tg_id, limit=10):
        session = self.Session()
        try:
            thoughts = (
                session.query(Thought)
                .filter_by(user_tg_id=user_tg_id)
                .order_by(Thought.datetime.desc())
                .limit(limit)
                .all()
            )
            return thoughts
        except Exception as e:
            logger.error(f"Error getting last thoughts: {e}")
            return []
        finally:
            session.close()

    def get_thoughts_by_type_and_date(self, type, start_date, end_date):
        """
        Retrieve thoughts filtered by type and a date range.

        :param type: The type of thoughts to retrieve ("dream", "thought", "plans").
        :param start_date: Start of the date range (datetime object).
        :param end_date: End of the date range (datetime object).
        :return: List of thoughts matching the criteria.
        """
        session = self.Session()
        try:
            thoughts = (
                session.query(Thought)
                .filter(Thought.type == type)
                .filter(Thought.datetime >= start_date)
                .filter(Thought.datetime <= end_date)
                .order_by(Thought.datetime.desc())
                .all()
            )

            if not thoughts:
                my_response = "No {type} found from {start_date} to {end_date}"
            else:
                my_response = (
                    f"<b>Here are your {type} from {start_date} to {end_date}:</b>\n"
                )

                for thought in thoughts:
                    my_response += (
                        f"<b>User:</b> {thought.username}\n"
                        f"<b>Date:</b> {thought.datetime.strftime('%Y-%m-%d')}\n"
                        f"<b>Type:</b> {thought.type}\n"
                        f"<b>Text:</b> {thought.text}\n\n"
                    )

            return my_response
        except Exception as e:
            logger.error(f"Error retrieving thoughts by type and date range: {e}")
            return []
        finally:
            session.close()


# Example usage (unchanged)
# if __name__ == "__main__":
#     db_connector = DatabaseConnector()

# db_connector.add_thought(123, "Dima", "This is my first thought.", "dream")
# db_connector.add_thought(123, "Dima", "Another thought here.", "thought")
# #     db_connector.add_thought(456, "Dima", "A thought from another user.")

# last_thoughts_user_123 = db_connector.get_last_thoughts(204039280)
# for thought in last_thoughts_user_123:
#     print(
#         f"User ID: {thought.user_tg_id}, Username: {thought.username}\n"
#         f"Time: {thought.datetime}  Type: {thought.type}, Text: { thought.text} "
#         f"Time: {thought.datetime.strftime("%Y-%m-%d") >= "2024-11-24"} "
#     )

# retreived_thoughts = db_connector.get_thoughts_by_type_and_date(
#     "thought", "2024-12-25", "2024-12-25"
# )

# thoughts_by_type_and_date = db_connector.get_thoughts_by_type_and_date(
#         type="thought",
#         start_date="2024-11-24",
#         end_date="2024-12-24",
#     )
# print(thoughts_by_type_and_date)

# for i in thoughts_by_type_and_date:
#     print(i.text, i.user)

#     # Simulate large db to test cleanup
#     for i in range(2000):
#         db_connector.add_thought(999, "Dima", f"Test thought {i}")

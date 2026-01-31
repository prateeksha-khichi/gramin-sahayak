"""
Database Manager - Handles PostgreSQL connections (Neon compatible)
"""

import os

from dotenv import load_dotenv

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from loguru import logger
from datetime import datetime
load_dotenv()




from .models import Base, User, LoanQuery, FraudCheck, RAGQuery, Conversation


class DatabaseManager:
    """
    Singleton database manager
    """

    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return

        self.database_url = os.getenv("DATABASE_URL")

        if not self.database_url:
            logger.warning("⚠️ DATABASE_URL not set, using SQLite fallback")
            self.database_url = "sqlite:///./gramin_sahayak.db"
            self.engine = create_engine(
                self.database_url,
                connect_args={"check_same_thread": False},
                echo=False
            )
        else:
            # 🔑 Neon fix: remove unsupported params
            if "channel_binding" in self.database_url:
                self.database_url = self.database_url.split("&channel_binding")[0]

            logger.info("🌐 Using Neon PostgreSQL database")

            self.engine = create_engine(
                self.database_url,
                echo=False,
                pool_pre_ping=True
            )

        self.SessionLocal = sessionmaker(bind=self.engine)

        # Create tables automatically
        self._create_tables()
        self._initialized = True

        logger.info("✅ Database initialized successfully")

    def _create_tables(self):
        """Create all tables"""
        try:
            Base.metadata.create_all(self.engine)
            logger.info("✅ Database tables created/verified")
        except Exception as e:
            logger.error(f"❌ Error creating tables: {e}")

    def get_session(self) -> Session:
        """Get a new database session"""
        return self.SessionLocal()

    # ---------------- USER OPERATIONS ---------------- #

    def get_or_create_user(self, telegram_id: str, **kwargs) -> User:
        session = self.get_session()
        try:
            user = session.query(User).filter_by(telegram_id=telegram_id).first()

            if not user:
                user = User(telegram_id=telegram_id, **kwargs)
                session.add(user)
                session.commit()
                logger.info(f"✅ New user created: {telegram_id}")
            else:
                user.last_active = datetime.utcnow()
                session.commit()

            return user
        finally:
            session.close()

    def save_loan_query(self, data: dict):
        session = self.get_session()
        try:
            session.add(LoanQuery(**data))
            session.commit()
        except Exception as e:
            logger.error(f"❌ Error saving loan query: {e}")
            session.rollback()
        finally:
            session.close()

    def save_fraud_check(self, data: dict):
        session = self.get_session()
        try:
            session.add(FraudCheck(**data))
            session.commit()
        except Exception as e:
            logger.error(f"❌ Error saving fraud check: {e}")
            session.rollback()
        finally:
            session.close()

    def save_rag_query(self, data: dict):
        session = self.get_session()
        try:
            session.add(RAGQuery(**data))
            session.commit()
        except Exception as e:
            logger.error(f"❌ Error saving RAG query: {e}")
            session.rollback()
        finally:
            session.close()

    def save_conversation(self, telegram_id, message_type, message_text, message_data=None):
        session = self.get_session()
        try:
            conv = Conversation(
                user_telegram_id=telegram_id,
                message_type=message_type,
                message_text=message_text,
                message_data=message_data
            )
            session.add(conv)
            session.commit()
        except Exception as e:
            logger.error(f"❌ Error saving conversation: {e}")
            session.rollback()
        finally:
            session.close()

    def get_user_stats(self, telegram_id: str) -> dict:
        session = self.get_session()
        try:
            return {
                "total_queries": session.query(RAGQuery).filter_by(user_telegram_id=telegram_id).count(),
                "loan_checks": session.query(LoanQuery).filter_by(user_telegram_id=telegram_id).count(),
                "fraud_checks": session.query(FraudCheck).filter_by(user_telegram_id=telegram_id).count()
            }
        finally:
            session.close()


# ✅ Global DB instance
db = DatabaseManager()

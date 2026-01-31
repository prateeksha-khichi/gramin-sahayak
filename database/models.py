"""
Database Models - PostgreSQL tables using SQLAlchemy
"""

from datetime import datetime
from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, Text, JSON
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()


class User(Base):
    """User table - stores user info"""
    __tablename__ = 'users'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    telegram_id = Column(String(50), unique=True, nullable=False)
    username = Column(String(100))
    first_name = Column(String(100))
    last_name = Column(String(100))
    phone_number = Column(String(20))
    language_preference = Column(String(10), default='hindi')
    created_at = Column(DateTime, default=datetime.utcnow)
    last_active = Column(DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f"<User {self.telegram_id} - {self.first_name}>"


class LoanQuery(Base):
    """Loan query history"""
    __tablename__ = 'loan_queries'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_telegram_id = Column(String(50), nullable=False)
    income = Column(Float)
    age = Column(Integer)
    employment_type = Column(String(50))
    credit_score = Column(Integer)
    loan_amount_requested = Column(Float)
    loan_purpose = Column(String(100))
    
    # Results
    eligible = Column(Boolean)
    recommended_amount = Column(Float)
    emi = Column(Float)
    interest_rate = Column(Float)
    confidence = Column(Float)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f"<LoanQuery {self.id} - User {self.user_telegram_id}>"


class FraudCheck(Base):
    """Fraud detection history"""
    __tablename__ = 'fraud_checks'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_telegram_id = Column(String(50), nullable=False)
    scheme_name = Column(String(200))
    scheme_description = Column(Text)
    
    # Results
    is_fraud = Column(Boolean)
    confidence = Column(Float)
    fraud_signals = Column(JSON)  # Store as JSON array
    verified = Column(Boolean)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f"<FraudCheck {self.id} - {self.scheme_name}>"


class RAGQuery(Base):
    """RAG chatbot query history"""
    __tablename__ = 'rag_queries'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_telegram_id = Column(String(50), nullable=False)
    question = Column(Text)
    answer = Column(Text)
    sources = Column(JSON)  # PDF sources used
    confidence = Column(Float)
    language = Column(String(10))
    
    created_at = Column(DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f"<RAGQuery {self.id} - User {self.user_telegram_id}>"


class Conversation(Base):
    """Conversation history for context"""
    __tablename__ = 'conversations'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_telegram_id = Column(String(50), nullable=False)
    message_type = Column(String(20))  # 'user', 'bot'
    message_text = Column(Text)
    message_data = Column(JSON)  # Additional structured data
    
    created_at = Column(DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f"<Conversation {self.id}>"
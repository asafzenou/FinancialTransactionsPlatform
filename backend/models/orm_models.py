"""
SQLAlchemy 2.0 ORM Models for Financial Transactions Platform

This module contains all database models with:
- Modern SQLAlchemy 2.0 syntax (DeclarativeBase, Mapped, mapped_column)
- Strict typing with type hints
- Data integrity constraints (not null, unique, foreign keys)
- Relationships for easy data access
"""

from datetime import datetime
from typing import Optional, List
from sqlalchemy import String, Integer, Float, DateTime, ForeignKey, UniqueConstraint, CheckConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from backend.database import Base


class Client(Base):
    """
    Client model - Represents a financial client/investor.
    
    Attributes:
        id: Unique client identifier (e.g., 'C001')
        transactions: List of transactions associated with this client
        positions: List of positions/holdings for this client
        violations: List of compliance violations for this client
    """
    __tablename__ = "clients"

    id: Mapped[str] = mapped_column(String(50), primary_key=True, index=True)
    
    transactions: Mapped[List["Transaction"]] = relationship(
        "Transaction",
        back_populates="client",
        cascade="all, delete-orphan",
        lazy="selectin"
    )
    positions: Mapped[List["Position"]] = relationship(
        "Position",
        back_populates="client",
        cascade="all, delete-orphan",
        lazy="selectin"
    )
    violations: Mapped[List["Violation"]] = relationship(
        "Violation",
        back_populates="client",
        cascade="all, delete-orphan",
        lazy="selectin"
    )

    def __repr__(self) -> str:
        return f"<Client(id={self.id})>"


class Transaction(Base):
    """
    Transaction model - Represents a financial transaction (buy/sell).
    
    Attributes:
        id: Auto-incremented primary key
        client_id: Foreign key to Client
        transaction_id_excel: Unique identifier from Excel import (prevents duplicates)
        isin: International Securities Identification Number
        action: 'buy' or 'sell'
        quantity: Number of units traded
        price: Price per unit at transaction time
        timestamp: When the transaction occurred
        client: Relationship to Client object
        violation: Relationship to associated Violation (if any)
    """
    __tablename__ = "transactions"
    
    # Positivity of quantity/price is enforced at the application layer via the
    # Invalid Values rule (Part D), which logs a violation rather than blocking
    # the insert at the DB level. Keeping a CHECK here would bypass the rule
    # and surface as an opaque 500 instead of a row in the violations table.
    __table_args__ = (
        UniqueConstraint('transaction_id_excel', name='uq_transaction_id_excel'),
        CheckConstraint("action IN ('buy', 'sell')", name='ck_transaction_action'),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    client_id: Mapped[str] = mapped_column(String(50), ForeignKey("clients.id", ondelete="CASCADE"), nullable=False, index=True)
    transaction_id_excel: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    isin: Mapped[str] = mapped_column(String(12), nullable=False, index=True)
    action: Mapped[str] = mapped_column(String(10), nullable=False)  # 'buy' or 'sell'
    quantity: Mapped[int] = mapped_column(Integer, nullable=False)
    price: Mapped[float] = mapped_column(Float, nullable=False)
    timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, index=True)

    # Relationships
    client: Mapped[Client] = relationship("Client", back_populates="transactions", lazy="joined")
    violations: Mapped[List["Violation"]] = relationship(
        "Violation",
        back_populates="transaction",
        cascade="all, delete-orphan",
        foreign_keys="Violation.transaction_id"
    )

    def __repr__(self) -> str:
        return f"<Transaction(id={self.id}, client_id={self.client_id}, action={self.action}, quantity={self.quantity})>"


class Position(Base):
    """
    Position model - Represents a client's current holding of a security.
    
    Attributes:
        id: Auto-incremented primary key
        client_id: Foreign key to Client
        isin: International Securities Identification Number
        total_quantity: Total number of units held
        average_price: Average purchase price per unit
        client: Relationship to Client object
    """
    __tablename__ = "positions"
    
    __table_args__ = (
        UniqueConstraint('client_id', 'isin', name='uq_client_isin'),
        CheckConstraint('total_quantity >= 0', name='ck_position_quantity_non_negative'),
        CheckConstraint('average_price > 0', name='ck_position_price_positive'),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    client_id: Mapped[str] = mapped_column(String(50), ForeignKey("clients.id", ondelete="CASCADE"), nullable=False, index=True)
    isin: Mapped[str] = mapped_column(String(12), nullable=False, index=True)
    total_quantity: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    average_price: Mapped[float] = mapped_column(Float, nullable=False)

    # Relationships
    client: Mapped[Client] = relationship("Client", back_populates="positions", lazy="joined")

    def __repr__(self) -> str:
        return f"<Position(id={self.id}, client_id={self.client_id}, isin={self.isin}, quantity={self.total_quantity})>"


class Violation(Base):
    """
    Violation model - Represents a compliance rule violation.
    
    Attributes:
        id: Auto-incremented primary key
        client_id: Foreign key to Client
        transaction_id: Optional foreign key to Transaction (nullable if violation isn't tied to a specific transaction)
        rule_broken: Name of the rule that was violated
        description: Detailed description of the violation
        timestamp: When the violation was detected (defaults to current UTC time)
        client: Relationship to Client object
        transaction: Relationship to Transaction object (optional)
    """
    __tablename__ = "violations"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    client_id: Mapped[str] = mapped_column(String(50), ForeignKey("clients.id", ondelete="CASCADE"), nullable=False, index=True)
    transaction_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("transactions.id", ondelete="SET NULL"), nullable=True, index=True)
    rule_broken: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    description: Mapped[str] = mapped_column(String(1000), nullable=False)
    timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, index=True, default=lambda: datetime.utcnow())

    # Relationships
    client: Mapped[Client] = relationship("Client", back_populates="violations", lazy="joined")
    transaction: Mapped[Optional[Transaction]] = relationship("Transaction", back_populates="violations", lazy="joined")

    def __repr__(self) -> str:
        return f"<Violation(id={self.id}, client_id={self.client_id}, rule={self.rule_broken})>"

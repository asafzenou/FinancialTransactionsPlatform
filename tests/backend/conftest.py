"""
Pytest configuration and fixtures with mocked database for Financial Transactions Platform.

Uses unittest.mock to mock all database access - no real database connections.
"""

import sys
import os
os.environ["TESTING"] = "True"
# Add project root to path so backend module can be imported
# conftest.py is at: project_root/tests/backend/conftest.py
conftest_dir = os.path.dirname(os.path.abspath(__file__))  # tests/backend
tests_dir = os.path.dirname(conftest_dir)  # tests
project_root = os.path.dirname(tests_dir)  # project root
sys.path.insert(0, project_root)

import pytest
from unittest.mock import Mock, MagicMock, patch
from datetime import datetime, timedelta
from typing import Generator

# Mock objects for database layers
@pytest.fixture(scope="function")
def mock_session() -> Mock:
    """Provide a mocked SQLAlchemy database session."""
    session = MagicMock()
    session.query = MagicMock(return_value=MagicMock())
    session.add = MagicMock()
    session.commit = MagicMock()
    session.refresh = MagicMock()
    session.close = MagicMock()
    return session


@pytest.fixture(scope="function")
def mock_client_dal(mock_session: Mock):
    """Provide a mocked ClientDAL instance."""
    from unittest.mock import MagicMock
    dal = MagicMock()
    dal.db = mock_session
    dal.create_client = MagicMock()
    dal.get_client_by_id = MagicMock()
    dal.get_all_clients = MagicMock()
    return dal


@pytest.fixture(scope="function")
def mock_transaction_dal(mock_session: Mock):
    """Provide a mocked TransactionDAL instance."""
    from unittest.mock import MagicMock
    dal = MagicMock()
    dal.db = mock_session
    dal.create_transaction = MagicMock()
    dal.get_transaction_by_excel_id = MagicMock(return_value=None)
    return dal


@pytest.fixture(scope="function")
def mock_violation_dal(mock_session: Mock):
    """Provide a mocked ViolationDAL instance."""
    from unittest.mock import MagicMock
    dal = MagicMock()
    dal.db = mock_session
    dal.create_violation = MagicMock()
    return dal


# ==================== GOLDEN TEST DATA FIXTURES (Mocked) ====================

@pytest.fixture(scope="function")
def golden_client():
    """
    Mocked golden client for baseline tests.
    
    Returns a mock Client object with no real database access.
    """
    client = Mock()
    client.id = "GOLD001"
    client.transactions = []
    client.positions = []
    client.violations = []
    return client


@pytest.fixture(scope="function")
def golden_transactions():
    """
    Mocked standard FIFO test dataset.
    
    Dataset:
    - ISIN: 'US0378331005' (Apple)
    - Transactions:
      1. BUY 100 @ $10.00 on 2024-01-01
      2. BUY 100 @ $20.00 on 2024-01-02
      3. SELL 150 @ $25.00 on 2024-01-03
    
    Expected result after FIFO:
    - Remaining position: 50 units @ $20.00
    - Realized P&L: (25-10)*100 + (25-20)*50 = 1500 + 250 = $1750
    """
    isin = 'US0378331005'
    base_time = datetime(2024, 1, 1, 10, 0, 0)
    
    tx1 = Mock()
    tx1.id = 1
    tx1.client_id = "GOLD001"
    tx1.transaction_id_excel = 'TX001'
    tx1.isin = isin
    tx1.action = 'buy'
    tx1.quantity = 100
    tx1.price = 10.00
    tx1.timestamp = base_time
    
    tx2 = Mock()
    tx2.id = 2
    tx2.client_id = "GOLD001"
    tx2.transaction_id_excel = 'TX002'
    tx2.isin = isin
    tx2.action = 'buy'
    tx2.quantity = 100
    tx2.price = 20.00
    tx2.timestamp = base_time + timedelta(days=1)
    
    tx3 = Mock()
    tx3.id = 3
    tx3.client_id = "GOLD001"
    tx3.transaction_id_excel = 'TX003'
    tx3.isin = isin
    tx3.action = 'sell'
    tx3.quantity = 150
    tx3.price = 25.00
    tx3.timestamp = base_time + timedelta(days=2)
    
    return {
        'client_id': "GOLD001",
        'isin': isin,
        'transactions': [tx1, tx2, tx3],
        'expected_remaining_qty': 50,
        'expected_remaining_price': 20.00,
        'expected_realized_pnl': 1750.0
    }


@pytest.fixture(scope="function")
def total_exit_scenario():
    """
    Mocked total exit scenario where all positions are sold.
    
    Dataset:
    - ISIN: 'GB0002374006' (Vodafone)
    - BUY 50 @ $5.00
    - SELL 50 @ $7.50
    
    Expected result:
    - Remaining position: 0 units
    - Realized P&L: (7.50 - 5.00) * 50 = $125.00
    """
    client_id = "TOTALEX001"
    isin = 'GB0002374006'
    base_time = datetime(2024, 2, 1, 10, 0, 0)
    
    buy_tx = Mock()
    buy_tx.id = 1
    buy_tx.client_id = client_id
    buy_tx.transaction_id_excel = 'TEX001'
    buy_tx.isin = isin
    buy_tx.action = 'buy'
    buy_tx.quantity = 50
    buy_tx.price = 5.00
    buy_tx.timestamp = base_time
    
    sell_tx = Mock()
    sell_tx.id = 2
    sell_tx.client_id = client_id
    sell_tx.transaction_id_excel = 'TEX002'
    sell_tx.isin = isin
    sell_tx.action = 'sell'
    sell_tx.quantity = 50
    sell_tx.price = 7.50
    sell_tx.timestamp = base_time + timedelta(hours=1)
    
    return {
        'client_id': client_id,
        'isin': isin,
        'buy_tx': buy_tx,
        'sell_tx': sell_tx,
        'expected_remaining_qty': 0,
        'expected_realized_pnl': 125.0
    }


@pytest.fixture(scope="function")
def multi_isin_portfolio():
    """
    Mocked portfolio with multiple ISINs for comprehensive analytics.
    
    Portfolio:
    - ISIN1: Apple (US0378331005) - Mixed buy/sell
    - ISIN2: Microsoft (US5949181045) - Only buys (unrealized P&L)
    - ISIN3: Google (US02079K3059) - Only sells (error position)
    """
    client_id = "MULTI001"
    isin1 = 'US0378331005'  # Apple
    isin2 = 'US5949181045'  # Microsoft
    isin3 = 'US02079K3059'  # Google
    
    base_time = datetime(2024, 3, 1, 10, 0, 0)
    
    txs = []
    
    # Apple: Buy and Sell
    tx1 = Mock()
    tx1.id = 1
    tx1.client_id = client_id
    tx1.isin = isin1
    tx1.action = 'buy'
    tx1.quantity = 200
    tx1.price = 150.00
    tx1.timestamp = base_time
    txs.append(tx1)
    
    tx2 = Mock()
    tx2.id = 2
    tx2.client_id = client_id
    tx2.isin = isin1
    tx2.action = 'sell'
    tx2.quantity = 100
    tx2.price = 160.00
    tx2.timestamp = base_time + timedelta(days=1)
    txs.append(tx2)
    
    # Microsoft: Only buys
    tx3 = Mock()
    tx3.id = 3
    tx3.client_id = client_id
    tx3.isin = isin2
    tx3.action = 'buy'
    tx3.quantity = 50
    tx3.price = 300.00
    tx3.timestamp = base_time + timedelta(days=2)
    txs.append(tx3)
    
    # Google: Only sells
    tx4 = Mock()
    tx4.id = 4
    tx4.client_id = client_id
    tx4.isin = isin3
    tx4.action = 'sell'
    tx4.quantity = 10
    tx4.price = 120.00
    tx4.timestamp = base_time + timedelta(days=3)
    txs.append(tx4)
    
    return {
        'client_id': client_id,
        'isin1': isin1,
        'isin2': isin2,
        'isin3': isin3,
        'transactions': txs,
        'expected_positions': {
            isin1: {'qty': 100, 'avg_price': 150.00},
            isin2: {'qty': 50, 'avg_price': 300.00}
        }
    }


@pytest.fixture(scope="function")
def day_trading_scenario():
    """
    Mocked day trading scenario with multiple buy/sell pairs within 24 hours.
    
    Dataset: 4 buy/sell pairs for same ISIN within 24 hours
    Expected: Day Trading violation triggered
    """
    client_id = "DAYTRADER001"
    isin = 'US0378331005'
    base_time = datetime(2024, 4, 1, 9, 30, 0)
    
    transactions = []
    for i in range(4):
        buy_time = base_time + timedelta(minutes=i*60)
        sell_time = buy_time + timedelta(minutes=30)
        
        buy_tx = Mock()
        buy_tx.id = i*2 + 1
        buy_tx.client_id = client_id
        buy_tx.isin = isin
        buy_tx.action = 'buy'
        buy_tx.quantity = 100
        buy_tx.price = 100.00 + i*10
        buy_tx.timestamp = buy_time
        transactions.append(buy_tx)
        
        sell_tx = Mock()
        sell_tx.id = i*2 + 2
        sell_tx.client_id = client_id
        sell_tx.isin = isin
        sell_tx.action = 'sell'
        sell_tx.quantity = 100
        sell_tx.price = 105.00 + i*10
        sell_tx.timestamp = sell_time
        transactions.append(sell_tx)
    
    return {
        'client_id': client_id,
        'isin': isin,
        'transactions': transactions,
        'day_trading_count': 4
    }


@pytest.fixture(scope="function")
def rounding_precision_scenario():
    """
    Mocked transactions with decimal prices to test rounding precision.
    
    Dataset:
    - BUY 3 @ $10.33333
    - SELL 2 @ $15.66666
    - Expected P&L: (15.66666 - 10.33333) * 2 = 10.66666
    """
    client_id = "ROUND001"
    isin = 'US1234567890'
    base_time = datetime(2024, 5, 1, 10, 0, 0)
    
    buy_tx = Mock()
    buy_tx.id = 1
    buy_tx.client_id = client_id
    buy_tx.isin = isin
    buy_tx.action = 'buy'
    buy_tx.quantity = 3
    buy_tx.price = 10.33333
    buy_tx.timestamp = base_time
    
    sell_tx = Mock()
    sell_tx.id = 2
    sell_tx.client_id = client_id
    sell_tx.isin = isin
    sell_tx.action = 'sell'
    sell_tx.quantity = 2
    sell_tx.price = 15.66666
    sell_tx.timestamp = base_time + timedelta(hours=1)
    
    return {
        'client_id': client_id,
        'isin': isin,
        'buy_tx': buy_tx,
        'sell_tx': sell_tx,
        'expected_realized_pnl': (15.66666 - 10.33333) * 2
    }


# ==================== DATA FACTORIES ====================

@pytest.fixture
def client_factory():
    """
    Factory fixture for creating mocked test clients dynamically.
    
    Usage:
        client = client_factory("C001")
        multiple_clients = [client_factory(f"C{i:03d}") for i in range(10)]
    """
    counter = 0
    
    def create_client(client_id: str = None) -> Mock:
        nonlocal counter
        if client_id is None:
            client_id = f"TEST_CLIENT_{counter:05d}"
            counter += 1
        
        client = Mock()
        client.id = client_id
        client.transactions = []
        client.positions = []
        client.violations = []
        return client
    
    return create_client


@pytest.fixture
def transaction_factory():
    """
    Factory fixture for creating mocked test transactions dynamically.
    
    Usage:
        tx = transaction_factory(client_id="C001", action="buy", quantity=100, price=50.00)
    """
    counter = 0
    
    def create_transaction(
        client_id: str,
        isin: str = 'US0378331005',
        action: str = 'buy',
        quantity: int = 100,
        price: float = 50.00,
        timestamp: datetime = None
    ) -> Mock:
        nonlocal counter
        if timestamp is None:
            timestamp = datetime(2024, 1, 1, 10, 0, 0) + timedelta(hours=counter)
        
        counter += 1
        
        tx = Mock()
        tx.id = counter
        tx.client_id = client_id
        tx.transaction_id_excel = f'TX_{counter:05d}'
        tx.isin = isin
        tx.action = action
        tx.quantity = quantity
        tx.price = price
        tx.timestamp = timestamp
        return tx
    
    return create_transaction


@pytest.fixture
def violation_factory():
    """
    Factory fixture for creating mocked test violations dynamically.
    
    Usage:
        violation = violation_factory(
            client_id="C001",
            rule_broken="Sell Before Buy",
            description="Client attempted to sell ISIN not in portfolio"
        )
    """
    counter = 0
    
    def create_violation(
        client_id: str,
        transaction_id: int = None,
        rule_broken: str = 'Test Violation',
        description: str = 'Test violation description',
        timestamp: datetime = None
    ) -> Mock:
        nonlocal counter
        if timestamp is None:
            timestamp = datetime(2024, 1, 1, 10, 0, 0) + timedelta(hours=counter)
        
        counter += 1
        
        violation = Mock()
        violation.id = counter
        violation.client_id = client_id
        violation.transaction_id = transaction_id
        violation.rule_broken = rule_broken
        violation.description = description
        violation.timestamp = timestamp
        return violation
    
    return create_violation


# ==================== MARKERS ====================

def pytest_configure(config):
    """Register custom pytest markers."""
    config.addinivalue_line("markers", "unit: Unit tests for business logic")
    config.addinivalue_line("markers", "integration: Integration tests for API endpoints")
    config.addinivalue_line("markers", "fifo: Tests for FIFO position calculation")
    config.addinivalue_line("markers", "violation: Tests for violation detection")
    config.addinivalue_line("markers", "validation: Tests for input validation")
    config.addinivalue_line("markers", "edge_case: Tests for edge cases")
    config.addinivalue_line("markers", "mock: Tests using mocked database")

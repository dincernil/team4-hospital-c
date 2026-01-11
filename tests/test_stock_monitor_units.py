import sys
import os
from unittest.mock import MagicMock
import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import stock_monitor.monitor as monitor


# =========================
# DB CONNECTION TESTS
# =========================

def test_get_db_connection_success(monkeypatch):
    fake_conn = MagicMock()
    monkeypatch.setattr(monitor.psycopg2, "connect", lambda **kwargs: fake_conn)
    conn = monitor.get_db_connection()
    assert conn is not None


def test_get_db_connection_failure(monkeypatch):
    monkeypatch.setattr(
        monitor.psycopg2,
        "connect",
        lambda **kw: (_ for _ in ()).throw(Exception("DB error"))
    )
    assert monitor.get_db_connection() is None


# =========================
# GET CURRENT STOCK
# =========================

def test_get_current_stock_success(monkeypatch):
    fake_cursor = MagicMock()
    fake_cursor.fetchone.return_value = (200, 79, 2.5)

    fake_conn = MagicMock()
    fake_conn.cursor.return_value = fake_cursor

    monkeypatch.setattr(monitor, "get_db_connection", lambda: fake_conn)

    stock = monitor.get_current_stock()
    assert stock["current_stock"] == 200
    assert stock["daily_consumption"] == 79
    assert stock["days_of_supply"] == 2.5


def test_get_current_stock_no_data(monkeypatch):
    fake_cursor = MagicMock()
    fake_cursor.fetchone.return_value = None

    fake_conn = MagicMock()
    fake_conn.cursor.return_value = fake_cursor

    monkeypatch.setattr(monitor, "get_db_connection", lambda: fake_conn)

    assert monitor.get_current_stock() is None


def test_get_current_stock_invalid_tuple(monkeypatch):
    """Coverage booster – invalid DB tuple"""
    fake_cursor = MagicMock()
    fake_cursor.fetchone.return_value = (200,)

    fake_conn = MagicMock()
    fake_conn.cursor.return_value = fake_cursor

    monkeypatch.setattr(monitor, "get_db_connection", lambda: fake_conn)

    assert monitor.get_current_stock() is None


def test_get_current_stock_db_connection_none(monkeypatch):
    monkeypatch.setattr(monitor, "get_db_connection", lambda: None)
    assert monitor.get_current_stock() is None


def test_get_current_stock_cursor_exception(monkeypatch):
    """Coverage booster – cursor exception"""
    fake_conn = MagicMock()
    fake_conn.cursor.side_effect = Exception("Cursor error")

    monkeypatch.setattr(monitor, "get_db_connection", lambda: fake_conn)
    assert monitor.get_current_stock() is None


# =========================
# DAILY CONSUMPTION
# =========================

def test_simulate_daily_consumption_normal():
    result = monitor.simulate_daily_consumption(100)
    assert isinstance(result, (int, float))


def test_simulate_daily_consumption_zero():
    assert monitor.simulate_daily_consumption(0) == 0


def test_simulate_daily_consumption_negative_input():
    """Coverage booster – negative input should not crash"""
    result = monitor.simulate_daily_consumption(-50)
    assert isinstance(result, (int, float))


# =========================
# THRESHOLD BREACH
# =========================

def test_check_threshold_breach_true(monkeypatch):
    monkeypatch.setattr(
        monitor,
        "get_current_stock",
        lambda: {
            "current_stock": 10,
            "daily_consumption": 10,
            "days_of_supply": 1.0
        }
    )

    breach, data = monitor.check_threshold_breach()
    assert breach is True
    assert data is not None


def test_check_threshold_breach_false(monkeypatch):
    monkeypatch.setattr(
        monitor,
        "get_current_stock",
        lambda: {
            "current_stock": 100,
            "daily_consumption": 10,
            "days_of_supply": 10.0
        }
    )

    breach, data = monitor.check_threshold_breach()
    assert breach is False
    assert data is None


def test_check_threshold_breach_equal_boundary(monkeypatch):
    monkeypatch.setattr(
        monitor,
        "get_current_stock",
        lambda: {
            "current_stock": 20,
            "daily_consumption": 10,
            "days_of_supply": 2.0
        }
    )

    breach, data = monitor.check_threshold_breach()
    assert breach is False
    assert data is None


def test_check_threshold_breach_no_stock(monkeypatch):
    monkeypatch.setattr(monitor, "get_current_stock", lambda: None)

    breach, data = monitor.check_threshold_breach()
    assert breach is False
    assert data is None


def test_check_threshold_breach_internal_exception(monkeypatch):
    """Coverage booster – expected exception"""

    def broken_get_current_stock():
        raise Exception("Unexpected error")

    monkeypatch.setattr(monitor, "get_current_stock", broken_get_current_stock)

    with pytest.raises(Exception):
        monitor.check_threshold_breach()



def test_get_db_connection_called_with_kwargs(monkeypatch):
    """Coverage booster – connect kwargs path"""

    called = {}

    def fake_connect(**kwargs):
        called.update(kwargs)
        return MagicMock()

    monkeypatch.setattr(monitor.psycopg2, "connect", fake_connect)

    conn = monitor.get_db_connection()
    assert conn is not None
    assert "host" in called
    assert "database" in called


def test_simulate_daily_consumption_spike(monkeypatch):
    """Coverage booster – spike branch"""

    monkeypatch.setattr(monitor.random, "random", lambda: 0.99)
    monkeypatch.setattr(monitor.random, "uniform", lambda a, b: b)

    result = monitor.simulate_daily_consumption(100)
    assert result >= 100

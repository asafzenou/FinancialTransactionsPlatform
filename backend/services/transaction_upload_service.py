"""
Transaction upload processing for the Financial Transactions Platform.

Implements Part D (Rule Violations) and Part E (Storage) of the assignment.

Rules and their treatment
-------------------------
ERROR rules (block insertion — the row never enters the `transactions` table):
    1. Invalid Values   (Quantity <= 0 or Price <= 0; unparseable rows)
    2. Sell Before Buy  (selling more units than the client currently holds)

WARNING rules (the trade is valid and IS persisted; the violation is also
recorded against the resulting transaction_id):
    3. Day Trading      (> 3 buy/sell pairs of the same ISIN in a rolling 24h window)
    4. Risk Concentration (a single ISIN > 50% of the client's portfolio value)

Processing model
----------------
* Rows are sorted by Timestamp before iteration so a 09:00 Buy is committed
  before its 09:05 Sell is evaluated.
* Each row is wrapped in try/except. Any DB failure triggers `db.rollback()`
  so a single bad row cannot poison the SQLAlchemy session for the remaining
  rows or leave SQLite in a locked state.
* Per-(client, ISIN) balance is tracked in memory and seeded from the DB on
  first reference, then updated immediately after each successful insert.
  This makes the Sell Before Buy check authoritative without re-querying the
  DB on every row.
* Uploads are append-only: duplicate Excel TransactionIds are skipped, all
  other rows extend prior state.
"""

from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
import math
import pandas as pd

from backend.dal.financial_dal import ClientDAL, TransactionDAL, ViolationDAL
from backend.schemas.financial_schemas import (
    TransactionCreate,
    ViolationCreate,
    ClientCreate,
)


CONCENTRATION_THRESHOLD_PCT = 50.0
DAY_TRADING_PAIR_LIMIT = 3        # > 3 pairs (i.e. 4+) triggers the violation
DAY_TRADING_WINDOW = timedelta(hours=24)

ERROR_RULES = {"Invalid Values", "Sell Before Buy"}
WARNING_RULES = {"Day Trading", "Risk Concentration"}


def _normalize_ts(ts: datetime) -> datetime:
    """Drop tzinfo so comparisons work regardless of how SQLite/pandas
    round-tripped the timestamp."""
    return ts.replace(tzinfo=None) if ts.tzinfo is not None else ts


class ViolationDetector:
    """Evaluates a parsed row against the 4 assignment rules.

    Reads prior committed transactions through the DAL, but the calling
    service feeds it an explicit `available_units` so the Sell Before Buy
    check sees in-flight balance changes from earlier rows in the same batch
    even before the next DAL query.
    """

    def __init__(self, db: Session):
        self.transaction_dal = TransactionDAL(db)

    def check_invalid_values(self, parsed: Dict, row_num: int) -> Optional[Dict]:
        # Use <=0 (not <0) so quantity/price of 0 are also rejected. A "buy 0
        # units" row is meaningless and would also fail any pre-existing
        # CheckConstraint on legacy databases.
        if parsed["quantity"] <= 0 or parsed["price"] <= 0:
            return {
                "rule": "Invalid Values",
                "description": (
                    f"Row {row_num}: Quantity={parsed['quantity']}, "
                    f"Price={parsed['price']}. Both must be > 0."
                ),
            }
        return None

    def check_sell_before_buy(
        self, parsed: Dict, row_num: int, available_units: int
    ) -> Optional[Dict]:
        if parsed["action"] != "sell":
            return None
        if parsed["quantity"] > available_units:
            return {
                "rule": "Sell Before Buy",
                "description": (
                    f"Row {row_num}: Attempting to sell {parsed['quantity']} "
                    f"units of {parsed['isin']}, but only "
                    f"{max(0, available_units)} available for client "
                    f"{parsed['client_id']}."
                ),
            }
        return None

    def check_day_trading(self, parsed: Dict, row_num: int) -> Optional[Dict]:
        ts = _normalize_ts(parsed["timestamp"])
        window_start = ts - DAY_TRADING_WINDOW

        history = self.transaction_dal.get_transactions_by_client_and_isin(
            parsed["client_id"], parsed["isin"]
        )
        in_window = [
            t for t in history
            if window_start < _normalize_ts(t.timestamp) <= ts
        ]

        buys = sum(1 for t in in_window if t.action == "buy")
        sells = sum(1 for t in in_window if t.action == "sell")

        if parsed["action"] == "buy":
            buys += 1
        else:
            sells += 1

        pairs = min(buys, sells)
        if pairs > DAY_TRADING_PAIR_LIMIT:
            return {
                "rule": "Day Trading",
                "description": (
                    f"Row {row_num}: client {parsed['client_id']} reached "
                    f"{pairs} buy/sell pairs of {parsed['isin']} within 24h "
                    f"(limit is {DAY_TRADING_PAIR_LIMIT})."
                ),
            }
        return None

    def check_risk_concentration(self, parsed: Dict, row_num: int) -> Optional[Dict]:
        if parsed["action"] != "buy":
            return None

        all_tx = self.transaction_dal.get_all_transactions_by_client(parsed["client_id"])

        total_value = sum(t.quantity * t.price for t in all_tx)
        isin_value = sum(t.quantity * t.price for t in all_tx if t.isin == parsed["isin"])

        current_value = parsed["quantity"] * parsed["price"]
        total_value += current_value
        isin_value += current_value

        if total_value <= 0:
            return None

        concentration = (isin_value / total_value) * 100
        if concentration > CONCENTRATION_THRESHOLD_PCT:
            return {
                "rule": "Risk Concentration",
                "description": (
                    f"Row {row_num}: Buying {parsed['isin']} would put "
                    f"{concentration:.1f}% of client {parsed['client_id']}'s "
                    f"portfolio in one ISIN (> {CONCENTRATION_THRESHOLD_PCT:.0f}%)."
                ),
            }
        return None


class TransactionUploadService:
    """Orchestrates a bulk upload: parse, sort, detect, persist."""

    def __init__(self, db: Session):
        self.db = db
        self.client_dal = ClientDAL(db)
        self.transaction_dal = TransactionDAL(db)
        self.violation_dal = ViolationDAL(db)
        self.detector = ViolationDetector(db)
        # Per-(client_id, isin) running balance, seeded from DB on first touch.
        self._balance: Dict[Tuple[str, str], int] = {}

    def process_dataframe(self, df: pd.DataFrame) -> Dict:
        success_count = 0
        violation_row_count = 0
        violations_logged = 0
        duplicate_count = 0
        errors: List[str] = []

        df = self._prepare_dataframe(df)

        for idx, row in df.iterrows():
            row_num = int(idx) + 2  # 1-indexed Excel row, accounting for header
            try:
                outcome = self._process_one_row(row, row_num)
            except Exception as exc:
                # Roll back so the session isn't poisoned for the next row.
                self.db.rollback()
                errors.append(f"Row {row_num}: unexpected error ({exc}).")
                violation_row_count += 1
                # Best-effort log of the unexpected failure as Invalid Values.
                self._log_unexpected_failure(row, row_num, str(exc))
                violations_logged += 1
                continue

            success_count += outcome["inserted"]
            duplicate_count += outcome["duplicate"]
            violation_row_count += outcome["violation_row"]
            violations_logged += outcome["violations_logged"]
            errors.extend(outcome["errors"])

        return {
            "success_count": success_count,
            "violation_row_count": violation_row_count,
            "violations_logged": violations_logged,
            "duplicate_count": duplicate_count,
            "errors": errors,
        }

    def _process_one_row(self, row: pd.Series, row_num: int) -> Dict:
        result = {
            "inserted": 0,
            "duplicate": 0,
            "violation_row": 0,
            "violations_logged": 0,
            "errors": [],
        }

        parsed, parse_error = self._parse_row(row, row_num)
        if parse_error is not None:
            client_id = self._safe_client_id(row)
            self._ensure_client(client_id)
            self._persist_violation(client_id, None, {
                "rule": "Invalid Values",
                "description": parse_error,
            })
            result["violation_row"] = 1
            result["violations_logged"] = 1
            result["errors"].append(parse_error)
            return result

        if self.transaction_dal.get_transaction_by_excel_id(parsed["transaction_id_excel"]):
            result["duplicate"] = 1
            return result

        # Run ERROR rules first (they block insertion).
        invalid = self.detector.check_invalid_values(parsed, row_num)
        if invalid:
            self._ensure_client(parsed["client_id"])
            self._persist_violation(parsed["client_id"], None, invalid)
            result["violation_row"] = 1
            result["violations_logged"] = 1
            result["errors"].append(f"Row {row_num}: {invalid['rule']}")
            return result

        available = self._get_balance(parsed["client_id"], parsed["isin"])
        sell_violation = self.detector.check_sell_before_buy(parsed, row_num, available)

        # WARNING rules — informational; do not block insertion.
        warning_violations = []
        for check in (
            self.detector.check_day_trading,
            self.detector.check_risk_concentration,
        ):
            v = check(parsed, row_num)
            if v:
                warning_violations.append(v)

        if sell_violation:
            self._ensure_client(parsed["client_id"])
            self._persist_violation(parsed["client_id"], None, sell_violation)
            for w in warning_violations:
                self._persist_violation(parsed["client_id"], None, w)
            result["violation_row"] = 1
            result["violations_logged"] = 1 + len(warning_violations)
            result["errors"].append(
                f"Row {row_num}: " + ", ".join(
                    v["rule"] for v in [sell_violation] + warning_violations
                )
            )
            return result

        # Clean ERROR-wise → insert the transaction.
        self._ensure_client(parsed["client_id"])
        try:
            tx = self.transaction_dal.create_transaction(
                TransactionCreate(
                    client_id=parsed["client_id"],
                    transaction_id_excel=parsed["transaction_id_excel"],
                    isin=parsed["isin"],
                    action=parsed["action"],
                    quantity=parsed["quantity"],
                    price=parsed["price"],
                    timestamp=parsed["timestamp"],
                )
            )
        except Exception as exc:
            self.db.rollback()
            self._persist_violation(parsed["client_id"], None, {
                "rule": "Invalid Values",
                "description": f"Row {row_num}: DB rejected insert ({exc}).",
            })
            result["violation_row"] = 1
            result["violations_logged"] = 1
            result["errors"].append(f"Row {row_num}: DB rejected insert ({exc})")
            return result

        # Update in-memory balance after successful insert.
        self._apply_balance_change(parsed["client_id"], parsed["isin"],
                                   parsed["action"], parsed["quantity"])
        result["inserted"] = 1

        if warning_violations:
            for w in warning_violations:
                self._persist_violation(parsed["client_id"], tx.id, w)
            result["violation_row"] = 1
            result["violations_logged"] = len(warning_violations)
            result["errors"].append(
                f"Row {row_num}: " + ", ".join(w["rule"] for w in warning_violations)
            )
        return result

    def _persist_violation(
        self, client_id: str, transaction_id: Optional[int], violation: Dict
    ) -> None:
        try:
            self.violation_dal.create_violation(
                ViolationCreate(
                    client_id=client_id,
                    transaction_id=transaction_id,
                    rule_broken=violation["rule"],
                    description=violation["description"],
                    timestamp=datetime.utcnow(),
                )
            )
        except Exception:
            self.db.rollback()
            raise

    def _log_unexpected_failure(self, row: pd.Series, row_num: int, exc_message: str) -> None:
        client_id = self._safe_client_id(row)
        try:
            self._ensure_client(client_id)
            self.violation_dal.create_violation(
                ViolationCreate(
                    client_id=client_id,
                    transaction_id=None,
                    rule_broken="Invalid Values",
                    description=f"Row {row_num}: unexpected error ({exc_message}).",
                    timestamp=datetime.utcnow(),
                )
            )
        except Exception:
            self.db.rollback()  # Swallow secondary failure — already logged in errors.

    # -------------------- DataFrame preparation --------------------

    def _prepare_dataframe(self, df: pd.DataFrame) -> pd.DataFrame:
        """Drop fully empty rows and sort by Timestamp (stable)."""
        cleaned = df.dropna(how="all")
        if "Timestamp" in cleaned.columns:
            parsed_ts = pd.to_datetime(cleaned["Timestamp"], errors="coerce")
            cleaned = (
                cleaned.assign(__sort_ts=parsed_ts)
                       .sort_values("__sort_ts", kind="mergesort", na_position="last")
                       .drop(columns="__sort_ts")
            )
        return cleaned.reset_index(drop=True)

    def _parse_row(self, row: pd.Series, row_num: int) -> Tuple[Optional[Dict], Optional[str]]:
        try:
            client_id = _to_str_id(row["ClientId"])
            tx_id = _to_str_id(row["TransactionId"])
            isin = _to_str_id(row["ISIN"])
            action = str(row["Action"]).strip().lower() if not _is_missing(row.get("Action")) else ""

            quantity = _to_int_strict(row["Quantity"])
            price = _to_float_strict(row["Price"])

            ts_raw = row["Timestamp"]
            if _is_missing(ts_raw):
                return None, f"Row {row_num}: Missing Timestamp."
            ts_pd = pd.to_datetime(ts_raw, errors="coerce")
            if pd.isna(ts_pd):
                return None, f"Row {row_num}: Could not parse Timestamp '{ts_raw}'."
            timestamp = ts_pd.to_pydatetime() if hasattr(ts_pd, "to_pydatetime") else ts_pd
        except (KeyError, ValueError, TypeError) as e:
            return None, f"Row {row_num}: Could not parse row ({e})."

        if not client_id:
            return None, f"Row {row_num}: Missing ClientId."
        if not tx_id:
            return None, f"Row {row_num}: Missing TransactionId."
        if not isin:
            return None, f"Row {row_num}: Missing ISIN."
        if action not in ("buy", "sell"):
            return None, (
                f"Row {row_num}: Action must be 'buy' or 'sell', "
                f"got '{row.get('Action')}'."
            )

        return {
            "client_id": client_id,
            "transaction_id_excel": tx_id,
            "isin": isin,
            "action": action,
            "quantity": quantity,
            "price": price,
            "timestamp": timestamp,
        }, None

    def _safe_client_id(self, row: pd.Series) -> str:
        try:
            cid = _to_str_id(row.get("ClientId"))
            return cid or "UNKNOWN"
        except Exception:
            return "UNKNOWN"

    def _ensure_client(self, client_id: str) -> None:
        if not self.client_dal.get_client_by_id(client_id):
            self.client_dal.create_client(ClientCreate(id=client_id))

    # -------------------- Balance state --------------------

    def _get_balance(self, client_id: str, isin: str) -> int:
        key = (client_id, isin)
        if key not in self._balance:
            prior = self.transaction_dal.get_transactions_by_client_and_isin(client_id, isin)
            bought = sum(t.quantity for t in prior if t.action == "buy")
            sold = sum(t.quantity for t in prior if t.action == "sell")
            self._balance[key] = bought - sold
        return self._balance[key]

    def _apply_balance_change(
        self, client_id: str, isin: str, action: str, quantity: int
    ) -> None:
        key = (client_id, isin)
        # Make sure the seed value is loaded before we mutate.
        self._get_balance(client_id, isin)
        if action == "buy":
            self._balance[key] += quantity
        else:
            self._balance[key] -= quantity


# -------------------- Pure parsing helpers --------------------

def _is_missing(value) -> bool:
    if value is None:
        return True
    try:
        return bool(pd.isna(value))
    except (TypeError, ValueError):
        return False


def _to_str_id(value) -> str:
    """Coerce an Excel cell to a clean string ID. `100.0` → `"100"`,
    NaN → `""`, otherwise stripped string."""
    if _is_missing(value):
        return ""
    if isinstance(value, float):
        if math.isfinite(value) and value.is_integer():
            return str(int(value))
        return str(value).strip()
    return str(value).strip()


def _to_int_strict(value) -> int:
    if _is_missing(value):
        raise ValueError("missing numeric value")
    if isinstance(value, bool):
        raise ValueError("bool is not a valid quantity")
    if isinstance(value, int):
        return value
    if isinstance(value, float):
        if not math.isfinite(value):
            raise ValueError("non-finite quantity")
        if not value.is_integer():
            raise ValueError(f"quantity must be a whole number, got {value}")
        return int(value)
    return int(str(value).strip())


def _to_float_strict(value) -> float:
    if _is_missing(value):
        raise ValueError("missing numeric value")
    if isinstance(value, bool):
        raise ValueError("bool is not a valid price")
    f = float(value)
    if not math.isfinite(f):
        raise ValueError("non-finite price")
    return f

from __future__ import annotations

import os
from typing import Any, Dict


def _env_bool(name: str, default: bool) -> bool:
    raw = os.getenv(name)
    if raw is None:
        return default
    return raw.strip().lower() in {"1", "true", "yes", "on"}


def _env_int(name: str, default: int) -> int:
    raw = os.getenv(name)
    if raw is None:
        return default
    try:
        return int(raw)
    except ValueError:
        return default


def _env_float(name: str, default: float) -> float:
    raw = os.getenv(name)
    if raw is None:
        return default
    try:
        return float(raw)
    except ValueError:
        return default


def _env_csv(name: str) -> list[str] | None:
    raw = os.getenv(name)
    if raw is None or raw.strip() == "":
        return None
    return [x.strip() for x in raw.split(",") if x.strip()]


def scanner_kwargs_from_env() -> Dict[str, Any]:
    """Build Scanner keyword arguments from environment variables."""
    return {
        "auto_select_strategy": _env_bool("SCANNER_AUTO_SELECT", True),
        "refresh_data": _env_bool("SCANNER_REFRESH_DATA", False),
        "start_date": os.getenv("SCANNER_START_DATE", "2023-01-01"),
        "lookback_days": _env_int("SCANNER_LOOKBACK_DAYS", 252),
        "selector_initial_capital": _env_float("SCANNER_SELECTOR_INITIAL_CAPITAL", 100_000.0),
        "selector_dd_penalty": _env_float("SCANNER_SELECTOR_DD_PENALTY", 1.0),
        "selector_walkforward_windows": _env_int("SCANNER_SELECTOR_WF_WINDOWS", 5),
        "selector_walkforward_validation_days": _env_int("SCANNER_SELECTOR_WF_VALID_DAYS", 63),
        "min_select_score": _env_float("SCANNER_MIN_SELECT_SCORE", 0.005),
        "switch_hysteresis": _env_float("SCANNER_SWITCH_HYSTERESIS", 0.01),
        "selection_log_path": os.getenv(
            "SCANNER_SELECTION_LOG_PATH",
            "paper_trading_results/strategy_selection_log.csv",
        ),
        "us_strategy_names": _env_csv("SCANNER_US_STRATEGIES"),
        "jp_strategy_names": _env_csv("SCANNER_JP_STRATEGIES"),
    }

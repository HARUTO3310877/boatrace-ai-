"""Tests for database models and loaders."""

import sqlite3
from pathlib import Path

import pandas as pd

from src.database.loader import init_db, load_entries, load_payouts, load_results


def test_init_db_in_memory_success() -> None:
    """インメモリ SQLite で初期化が成功することを確認する。"""
    init_db(":memory:")


def test_load_and_idempotency(tmp_path: Path) -> None:
    """サンプルデータ投入と冪等性を確認する。"""
    db_path = tmp_path / "boatrace.db"

    entries_df = pd.DataFrame(
        [
            {
                "race_date": "2025-01-01",
                "venue_code": 1,
                "race_number": 1,
                "lane": 1,
                "player_id": 123456,
                "player_name": "山田太郎",
                "age": 34,
                "branch": "東京",
                "weight": 51.5,
                "class_rank": "A1",
                "win_rate_national": 6.5,
                "top2_rate_national": 45.0,
                "win_rate_local": 6.1,
                "top2_rate_local": 42.0,
                "motor_no": 12,
                "motor_top2_rate": 38.5,
                "boat_no": 34,
                "boat_top2_rate": 40.1,
            }
        ]
    )
    results_df = pd.DataFrame(
        [
            {
                "race_date": "2025-01-01",
                "venue_code": 1,
                "race_number": 1,
                "lane": 1,
                "finish_position": 1,
                "course_position": 1,
                "start_timing": 0.14,
                "race_time": "1:49.2",
                "winning_technique": "逃げ",
                "weather": "晴",
                "wind_direction": "北",
                "wind_speed": 5.0,
                "wave_height": 2.0,
                "temperature": 18.0,
                "water_temperature": 20.0,
            }
        ]
    )
    payouts_df = pd.DataFrame(
        [
            {
                "race_date": "2025-01-01",
                "venue_code": 1,
                "race_number": 1,
                "tansho_combo": "1",
                "tansho_payout": 120,
                "rentan2_combo": "1-2",
                "rentan2_payout": 340,
                "rentan3_combo": "1-2-3",
                "rentan3_payout": 1230,
            }
        ]
    )

    load_entries(entries_df, str(db_path))
    load_results(results_df, str(db_path))
    load_payouts(payouts_df, str(db_path))

    with sqlite3.connect(db_path) as conn:
        race_count = conn.execute("SELECT COUNT(*) FROM races").fetchone()[0]
        entry_count = conn.execute("SELECT COUNT(*) FROM entries").fetchone()[0]
        result_count = conn.execute("SELECT COUNT(*) FROM results").fetchone()[0]
        payout_count = conn.execute("SELECT COUNT(*) FROM payouts").fetchone()[0]

    assert race_count == 1
    assert entry_count == 1
    assert result_count == 1
    assert payout_count == 1

    load_entries(entries_df, str(db_path))
    load_results(results_df, str(db_path))
    load_payouts(payouts_df, str(db_path))

    with sqlite3.connect(db_path) as conn:
        race_count_2 = conn.execute("SELECT COUNT(*) FROM races").fetchone()[0]
        entry_count_2 = conn.execute("SELECT COUNT(*) FROM entries").fetchone()[0]
        result_count_2 = conn.execute("SELECT COUNT(*) FROM results").fetchone()[0]
        payout_count_2 = conn.execute("SELECT COUNT(*) FROM payouts").fetchone()[0]

    assert race_count_2 == 1
    assert entry_count_2 == 1
    assert result_count_2 == 1
    assert payout_count_2 == 1

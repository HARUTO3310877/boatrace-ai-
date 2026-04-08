"""SQLite へのデータ投入ユーティリティ。"""

from __future__ import annotations

import math
import sqlite3
from datetime import date, datetime

import pandas as pd
from sqlalchemy import create_engine

from src.database.models import Base


def _sqlite_connect(db_path: str) -> sqlite3.Connection:
    """SQLite 接続を返す。"""
    if db_path == ":memory:":
        return sqlite3.connect(":memory:")
    return sqlite3.connect(db_path)


def _normalize_value(value: object) -> object:
    """NaN を None に変換する。"""
    if value is None:
        return None
    if isinstance(value, float) and math.isnan(value):
        return None
    return value


def _parse_date(value: object) -> str:
    """日付値を SQLite 格納用 ISO 文字列へ変換する。"""
    if isinstance(value, date):
        return value.isoformat()
    text = str(value)
    if len(text) == 8 and text.isdigit():
        return datetime.strptime(text, "%Y%m%d").date().isoformat()
    return datetime.strptime(text, "%Y-%m-%d").date().isoformat()


def _build_race_id(row: pd.Series) -> str:
    """row から race_id を生成する。"""
    date_text = str(row["race_date"])
    if len(date_text) == 10 and "-" in date_text:
        date_text = date_text.replace("-", "")
    return f"{date_text}_{int(row['venue_code'])}_{int(row['race_number'])}"


def _race_time_to_seconds(value: object) -> float | None:
    """タイム文字列を秒へ変換する。"""
    if value is None:
        return None
    if isinstance(value, float):
        if math.isnan(value):
            return None
        return value
    text = str(value).strip()
    if not text:
        return None
    if ":" in text:
        minute_text, sec_text = text.split(":", maxsplit=1)
        try:
            return int(minute_text) * 60 + float(sec_text)
        except ValueError:
            return None
    try:
        return float(text)
    except ValueError:
        return None


def init_db(db_path: str) -> None:
    """SQLite にテーブルを作成する。

    Args:
        db_path: SQLite ファイルパス。
    """
    if db_path == ":memory:":
        engine = create_engine("sqlite+pysqlite:///:memory:")
    else:
        engine = create_engine(f"sqlite+pysqlite:///{db_path}")
    Base.metadata.create_all(engine)


def load_entries(df: pd.DataFrame, db_path: str) -> None:
    """番組表 DataFrame を races / entries テーブルへ投入する。

    Args:
        df: 番組表 DataFrame。
        db_path: SQLite ファイルパス。
    """
    init_db(db_path)
    with _sqlite_connect(db_path) as conn:
        for _, row in df.iterrows():
            race_id = _build_race_id(row)
            conn.execute(
                """
                INSERT OR REPLACE INTO races (race_id, race_date, venue_code, race_number)
                VALUES (?, ?, ?, ?)
                """,
                (
                    race_id,
                    _parse_date(row["race_date"]),
                    _normalize_value(row["venue_code"]),
                    _normalize_value(row["race_number"]),
                ),
            )
            conn.execute(
                """
                INSERT OR REPLACE INTO entries (
                    race_id, lane, player_id, player_name, age, branch, weight, class_rank,
                    win_rate_national, top2_rate_national, win_rate_local, top2_rate_local,
                    motor_no, motor_top2_rate, boat_no, boat_top2_rate
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    race_id,
                    _normalize_value(row["lane"]),
                    _normalize_value(row["player_id"]),
                    _normalize_value(row["player_name"]),
                    _normalize_value(row["age"]),
                    _normalize_value(row["branch"]),
                    _normalize_value(row["weight"]),
                    _normalize_value(row["class_rank"]),
                    _normalize_value(row["win_rate_national"]),
                    _normalize_value(row["top2_rate_national"]),
                    _normalize_value(row["win_rate_local"]),
                    _normalize_value(row["top2_rate_local"]),
                    _normalize_value(row["motor_no"]),
                    _normalize_value(row["motor_top2_rate"]),
                    _normalize_value(row["boat_no"]),
                    _normalize_value(row["boat_top2_rate"]),
                ),
            )


def load_results(df: pd.DataFrame, db_path: str) -> None:
    """成績 DataFrame を races / results テーブルへ投入する。

    Args:
        df: 成績 DataFrame。
        db_path: SQLite ファイルパス。
    """
    init_db(db_path)
    with _sqlite_connect(db_path) as conn:
        for _, row in df.iterrows():
            race_id = _build_race_id(row)
            conn.execute(
                """
                INSERT OR REPLACE INTO races (
                    race_id, race_date, venue_code, race_number,
                    weather, wind_direction, wind_speed, wave_height, temperature, water_temperature
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    race_id,
                    _parse_date(row["race_date"]),
                    _normalize_value(row["venue_code"]),
                    _normalize_value(row["race_number"]),
                    _normalize_value(row.get("weather")),
                    _normalize_value(row.get("wind_direction")),
                    _normalize_value(row.get("wind_speed")),
                    _normalize_value(row.get("wave_height")),
                    _normalize_value(row.get("temperature")),
                    _normalize_value(row.get("water_temperature")),
                ),
            )
            conn.execute(
                """
                INSERT OR REPLACE INTO results (
                    race_id, lane, finish_position, course_position,
                    start_timing, race_time, winning_technique
                ) VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    race_id,
                    _normalize_value(row["lane"]),
                    _normalize_value(row.get("finish_position")),
                    _normalize_value(row.get("course_position")),
                    _normalize_value(row.get("start_timing")),
                    _race_time_to_seconds(row.get("race_time")),
                    _normalize_value(row.get("winning_technique")),
                ),
            )


def load_payouts(df: pd.DataFrame, db_path: str) -> None:
    """払戻金 DataFrame を payouts テーブルへ投入する。

    Args:
        df: 払戻金 DataFrame。
        db_path: SQLite ファイルパス。
    """
    init_db(db_path)
    with _sqlite_connect(db_path) as conn:
        for _, row in df.iterrows():
            race_id = _build_race_id(row)
            conn.execute(
                """
                INSERT OR REPLACE INTO races (race_id, race_date, venue_code, race_number)
                VALUES (?, ?, ?, ?)
                """,
                (
                    race_id,
                    _parse_date(row["race_date"]),
                    _normalize_value(row["venue_code"]),
                    _normalize_value(row["race_number"]),
                ),
            )
            conn.execute(
                """
                INSERT OR REPLACE INTO payouts (
                    race_id, tansho_combo, tansho_payout,
                    rentan2_combo, rentan2_payout, rentan3_combo, rentan3_payout
                ) VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    race_id,
                    _normalize_value(row.get("tansho_combo")),
                    _normalize_value(row.get("tansho_payout")),
                    _normalize_value(row.get("rentan2_combo")),
                    _normalize_value(row.get("rentan2_payout")),
                    _normalize_value(row.get("rentan3_combo")),
                    _normalize_value(row.get("rentan3_payout")),
                ),
            )

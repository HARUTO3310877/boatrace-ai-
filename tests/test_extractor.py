"""Tests for src.collector.extractor."""

import pandas as pd

from src.collector.extractor import normalize_fullwidth, parse_bangumi, parse_results


def _build_bangumi_line(weight: str = "51.5") -> str:
    parts = [
        "20250101",  # race_date (8)
        "01",  # venue_code (2)
        "01",  # race_number (2)
        "1",  # lane (1)
        "123456",  # player_id (6)
        "山田太郎".ljust(16),  # player_name (16)
        "34",  # age (2)
        "東京  ",  # branch (4)
        f"{weight:>4}",  # weight (4)
        "A1",  # class_rank (2)
        "6.50",  # win_rate_national (4)
        "45.0",  # top2_rate_national (4)
        "6.10",  # win_rate_local (4)
        "42.0",  # top2_rate_local (4)
        "12",  # motor_no (2)
        "38.5",  # motor_top2_rate (4)
        "34",  # boat_no (2)
        "40.1",  # boat_top2_rate (4)
    ]
    return "".join(parts)


def _build_result_line(start_timing: str = "0.14") -> str:
    parts = [
        "20250101",  # race_date (8)
        "01",  # venue_code (2)
        "01",  # race_number (2)
        "1",  # lane (1)
        "123456",  # player_id (6)
        "1",  # finish_position (1)
        "01:49.2 ",  # race_time (8)
        "1",  # course_position (1)
        f"{start_timing:>4}",  # start_timing (4)
        "逃げ    ",  # winning_technique (8)
        "晴れ  ",  # weather (4)
        "北   ",  # wind_direction (4)
        "005",  # wind_speed (3)
        "002",  # wave_height (3)
        "018",  # temperature (3)
        "020",  # water_temperature (3)
        "1-1",  # tansho_combo (3)
        "001200",  # tansho_payout (6)
        "1-2  ",  # rentan2_combo (5)
        "003400",  # rentan2_payout (6)
        "1-2-3  ",  # rentan3_combo (7)
        "0123000",  # rentan3_payout (7)
    ]
    return "".join(parts)


def test_normalize_fullwidth() -> None:
    """全角数字が半角数字へ変換されることを確認する。"""
    assert normalize_fullwidth("１２３４５") == "12345"


def test_parse_fixed_width_columns_and_types() -> None:
    """固定長テキストが期待カラム数でパースされることを確認する。"""
    bangumi_df = parse_bangumi(_build_bangumi_line())
    results_df = parse_results(_build_result_line())

    assert bangumi_df.shape[1] == 18
    assert results_df.shape[1] == 16

    assert pd.api.types.is_numeric_dtype(bangumi_df["race_number"])
    assert pd.api.types.is_numeric_dtype(bangumi_df["weight"])
    assert pd.api.types.is_numeric_dtype(results_df["start_timing"])


def test_invalid_data_converted_to_nan() -> None:
    """不正な固定長値が NaN として取り込まれることを確認する。"""
    bangumi_df = parse_bangumi(_build_bangumi_line(weight="ABCD"))
    results_df = parse_results(_build_result_line(start_timing="ABCD"))

    assert pd.isna(bangumi_df.loc[0, "weight"])
    assert pd.isna(results_df.loc[0, "start_timing"])

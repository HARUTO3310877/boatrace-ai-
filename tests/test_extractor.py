"""Tests for src.collector.extractor."""

from pathlib import Path
from unittest.mock import patch

import pandas as pd

from src.collector.extractor import extract_lzh, normalize_fullwidth, parse_bangumi, parse_results

RESULT_SAMPLE_TEXT = """STARTK
24KBGN
2025/01/01 大村[成績]
 1R          予選                      H1800m  晴    風  北    3m  波    2cm
 着  艇 登番     選  手  名     モーター ホ ート 展示  進入  スタートタイミング レースタイム  逃げ
---------------------------------------------------------------------------------
 01  1 3501 川　上　　昇　平 50   12 6.89  1     0.08      1.49.7
 02  3 4299 中　島　　浩　哉 59   49 6.87  3     0.08      1.50.1
 03  6 3773 津　留　浩一郎 57   25 6.77  6     0.11      1.51.3
 04  5 4393 田　中　　孝　明 31   45 6.86  5     0.09      1.51.6
 05  2 5129 山　口　真喜子 46   61 6.83  2     0.13      .  .
 06  4 4855 江　頭　　賢　太 18   67 6.83  4     0.21      .  .
"""


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
    results_df = parse_results(RESULT_SAMPLE_TEXT)

    assert bangumi_df.shape[1] == 18
    assert results_df.shape[1] == 16

    assert pd.api.types.is_numeric_dtype(bangumi_df["race_number"])
    assert pd.api.types.is_numeric_dtype(bangumi_df["weight"])
    assert pd.api.types.is_numeric_dtype(results_df["start_timing"])
    assert len(results_df) == 6
    assert results_df.loc[0, "race_number"] == 1
    assert results_df.loc[0, "weather"] == "晴"
    assert results_df.loc[0, "wind_direction"] == "北"
    assert results_df.loc[0, "wind_speed"] == 3.0
    assert results_df.loc[0, "wave_height"] == 2.0
    assert results_df.loc[0, "race_time"] == 109.7


def test_invalid_data_converted_to_nan() -> None:
    """不正な固定長値が NaN として取り込まれることを確認する。"""
    bangumi_df = parse_bangumi(_build_bangumi_line(weight="ABCD"))
    results_df = parse_results(RESULT_SAMPLE_TEXT)

    assert pd.isna(bangumi_df.loc[0, "weight"])
    assert pd.isna(results_df.loc[4, "race_time"])
    assert pd.isna(results_df.loc[5, "race_time"])


@patch("src.collector.extractor.subprocess.run")
@patch("src.collector.extractor.shutil.which", return_value="7z")
def test_extract_lzh_uses_7z_command(mock_which: object, mock_run: object, tmp_path: Path) -> None:
    """extract_lzh が 7z コマンドで解凍・読込することを確認する。"""
    lzh_path = tmp_path / "sample.lzh"
    lzh_path.write_bytes(b"dummy")

    def fake_run(*args: object, **kwargs: object) -> None:
        out_opt = [str(a) for a in args[0] if str(a).startswith("-o")][0]
        out_dir = Path(out_opt[2:])
        (out_dir / "sample.txt").write_text("テスト", encoding="cp932")

    mock_run.side_effect = fake_run
    texts = extract_lzh(str(lzh_path))

    assert texts == ["テスト"]
    assert mock_which is not None
    assert mock_run is not None

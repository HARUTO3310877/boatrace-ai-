"""LZH 解凍および固定長テキスト解析モジュール。"""

from __future__ import annotations

import logging
import shutil
import subprocess
import tempfile
import unicodedata
from pathlib import Path
from typing import Callable

import pandas as pd

LOGGER = logging.getLogger(__name__)

BANGUMI_COLUMNS = [
    "race_date",
    "venue_code",
    "race_number",
    "lane",
    "player_id",
    "player_name",
    "age",
    "branch",
    "weight",
    "class_rank",
    "win_rate_national",
    "top2_rate_national",
    "win_rate_local",
    "top2_rate_local",
    "motor_no",
    "motor_top2_rate",
    "boat_no",
    "boat_top2_rate",
]

RESULT_COLUMNS = [
    "race_date",
    "venue_code",
    "race_number",
    "lane",
    "player_id",
    "finish_position",
    "race_time",
    "course_position",
    "start_timing",
    "winning_technique",
    "weather",
    "wind_direction",
    "wind_speed",
    "wave_height",
    "temperature",
    "water_temperature",
]

PAYOUT_COLUMNS = [
    "race_date",
    "venue_code",
    "race_number",
    "tansho_combo",
    "tansho_payout",
    "rentan2_combo",
    "rentan2_payout",
    "rentan3_combo",
    "rentan3_payout",
]


def normalize_fullwidth(text: str) -> str:
    """全角文字を半角へ正規化する。

    Args:
        text: 正規化対象の文字列。

    Returns:
        正規化後の文字列。
    """
    return unicodedata.normalize("NFKC", text)


def _slice(line: str, start: int, end: int) -> str:
    """固定長の位置指定で文字列を切り出して正規化する。"""
    return normalize_fullwidth(line[start:end]).strip()


def _to_int(value: str) -> float:
    """文字列を int へ変換し、失敗時は NaN を返す。"""
    if not value:
        return float("nan")
    try:
        return int(value)
    except ValueError:
        return float("nan")


def _to_float(value: str) -> float:
    """文字列を float へ変換し、失敗時は NaN を返す。"""
    if not value:
        return float("nan")
    try:
        return float(value)
    except ValueError:
        return float("nan")


def _should_skip_header(line: str) -> bool:
    """ヘッダ行などの非データ行を判定する。"""
    stripped = normalize_fullwidth(line).strip()
    if not stripped:
        return True
    return not stripped[:8].isdigit()


def extract_lzh(lzh_path: str) -> list[str]:
    """LZH ファイルを解凍しテキストコンテンツを返す。

    Args:
        lzh_path: LZH ファイルパス。

    Returns:
        解凍されたテキストファイルの内容リスト。

    Raises:
        FileNotFoundError: 7z コマンドが見つからない場合。
        subprocess.CalledProcessError: 解凍コマンドが失敗した場合。
    """
    windows_7z = r"C:\Program Files\7-Zip\7z.exe"
    seven_zip = windows_7z if Path(windows_7z).exists() else shutil.which("7z")
    if not seven_zip:
        raise FileNotFoundError("7z command not found. Install 7-Zip or add 7z to PATH.")

    texts: list[str] = []
    with tempfile.TemporaryDirectory() as tmp_dir:
        subprocess.run(
            [seven_zip, "x", "-y", lzh_path, f"-o{tmp_dir}"],
            check=True,
            capture_output=True,
            text=True,
        )
        for extracted in sorted(Path(tmp_dir).rglob("*")):
            if extracted.is_file():
                texts.append(extracted.read_text(encoding="cp932", errors="replace"))
    return texts


def parse_bangumi(text: str) -> pd.DataFrame:
    """番組表の固定長テキストを DataFrame に変換する。

    Args:
        text: 番組表テキスト。

    Returns:
        番組表 DataFrame。
    """
    rows: list[dict[str, object]] = []
    for line_no, line in enumerate(text.splitlines(), start=1):
        if _should_skip_header(line):
            continue
        try:
            row = {
                "race_date": _slice(line, 0, 8),
                "venue_code": _slice(line, 8, 10),
                "race_number": _to_int(_slice(line, 10, 12)),
                "lane": _to_int(_slice(line, 12, 13)),
                "player_id": _to_int(_slice(line, 13, 19)),
                "player_name": _slice(line, 19, 35),
                "age": _to_int(_slice(line, 35, 37)),
                "branch": _slice(line, 37, 41),
                "weight": _to_float(_slice(line, 41, 45)),
                "class_rank": _slice(line, 45, 47),
                "win_rate_national": _to_float(_slice(line, 47, 51)),
                "top2_rate_national": _to_float(_slice(line, 51, 55)),
                "win_rate_local": _to_float(_slice(line, 55, 59)),
                "top2_rate_local": _to_float(_slice(line, 59, 63)),
                "motor_no": _to_int(_slice(line, 63, 65)),
                "motor_top2_rate": _to_float(_slice(line, 65, 69)),
                "boat_no": _to_int(_slice(line, 69, 71)),
                "boat_top2_rate": _to_float(_slice(line, 71, 75)),
            }
            rows.append(row)
        except Exception as exc:  # noqa: BLE001
            LOGGER.exception("Failed to parse bangumi line %s: %s", line_no, exc)
    return pd.DataFrame(rows, columns=BANGUMI_COLUMNS)


def parse_results(text: str) -> pd.DataFrame:
    """競走成績の固定長テキストを DataFrame に変換する。

    Args:
        text: 競走成績テキスト。

    Returns:
        競走成績 DataFrame。
    """
    rows: list[dict[str, object]] = []
    for line_no, line in enumerate(text.splitlines(), start=1):
        if _should_skip_header(line):
            continue
        try:
            row = {
                "race_date": _slice(line, 0, 8),
                "venue_code": _slice(line, 8, 10),
                "race_number": _to_int(_slice(line, 10, 12)),
                "lane": _to_int(_slice(line, 12, 13)),
                "player_id": _to_int(_slice(line, 13, 19)),
                "finish_position": _to_int(_slice(line, 19, 20)),
                "race_time": _slice(line, 20, 28),
                "course_position": _to_int(_slice(line, 28, 29)),
                "start_timing": _to_float(_slice(line, 29, 33)),
                "winning_technique": _slice(line, 33, 41),
                "weather": _slice(line, 41, 45),
                "wind_direction": _slice(line, 45, 49),
                "wind_speed": _to_float(_slice(line, 49, 52)),
                "wave_height": _to_float(_slice(line, 52, 55)),
                "temperature": _to_float(_slice(line, 55, 58)),
                "water_temperature": _to_float(_slice(line, 58, 61)),
            }
            rows.append(row)
        except Exception as exc:  # noqa: BLE001
            LOGGER.exception("Failed to parse result line %s: %s", line_no, exc)
    return pd.DataFrame(rows, columns=RESULT_COLUMNS)


def parse_payouts(text: str) -> pd.DataFrame:
    """競走成績テキストから払戻金テーブルを抽出する。

    Args:
        text: 競走成績テキスト。

    Returns:
        払戻金 DataFrame。
    """
    rows: list[dict[str, object]] = []
    for line_no, line in enumerate(text.splitlines(), start=1):
        if _should_skip_header(line):
            continue
        try:
            row = {
                "race_date": _slice(line, 0, 8),
                "venue_code": _slice(line, 8, 10),
                "race_number": _to_int(_slice(line, 10, 12)),
                "tansho_combo": _slice(line, 61, 64),
                "tansho_payout": _to_int(_slice(line, 64, 70)),
                "rentan2_combo": _slice(line, 70, 75),
                "rentan2_payout": _to_int(_slice(line, 75, 81)),
                "rentan3_combo": _slice(line, 81, 88),
                "rentan3_payout": _to_int(_slice(line, 88, 95)),
            }
            rows.append(row)
        except Exception as exc:  # noqa: BLE001
            LOGGER.exception("Failed to parse payout line %s: %s", line_no, exc)
    return pd.DataFrame(rows, columns=PAYOUT_COLUMNS)


def batch_parse(input_dir: str, data_type: str) -> pd.DataFrame:
    """ディレクトリ内の LZH ファイルを一括パースして結合する。

    Args:
        input_dir: LZH 入力ディレクトリ。
        data_type: ``bangumi`` / ``results`` / ``payouts``。

    Returns:
        結合後の DataFrame。

    Raises:
        ValueError: 不正な ``data_type`` が渡された場合。
    """
    parser_map: dict[str, Callable[[str], pd.DataFrame]] = {
        "bangumi": parse_bangumi,
        "results": parse_results,
        "payouts": parse_payouts,
    }
    if data_type not in parser_map:
        raise ValueError("data_type must be one of: bangumi, results, payouts")

    frames: list[pd.DataFrame] = []
    for lzh_file in sorted(Path(input_dir).glob("*.lzh")):
        try:
            for text in extract_lzh(str(lzh_file)):
                frames.append(parser_map[data_type](text))
        except Exception as exc:  # noqa: BLE001
            LOGGER.exception("Failed to parse file %s: %s", lzh_file, exc)

    if not frames:
        return pd.DataFrame(columns=parser_map[data_type]("").columns)
    return pd.concat(frames, ignore_index=True)

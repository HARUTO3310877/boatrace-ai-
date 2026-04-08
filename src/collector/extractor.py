"""LZH 解凍および固定長テキスト解析モジュール。"""

from __future__ import annotations

import logging
import re
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

VENUE_CODE_MAP = {
    "桐生": "01",
    "戸田": "02",
    "江戸川": "03",
    "平和島": "04",
    "多摩川": "05",
    "浜名湖": "06",
    "蒲郡": "07",
    "常滑": "08",
    "津": "09",
    "三国": "10",
    "びわこ": "11",
    "住之江": "12",
    "尼崎": "13",
    "鳴門": "14",
    "丸亀": "15",
    "児島": "16",
    "宮島": "17",
    "徳山": "18",
    "下関": "19",
    "若松": "20",
    "芦屋": "21",
    "福岡": "22",
    "唐津": "23",
    "大村": "24",
}


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


def _extract_file_context(text: str) -> tuple[str, str]:
    """テキストヘッダから開催日と会場コードを抽出する。"""
    normalized = normalize_fullwidth(text)
    date_match = re.search(r"(20\d{2})[/-]?(\d{2})[/-]?(\d{2})", normalized)
    race_date = "".join(date_match.groups()) if date_match else ""

    venue_code = ""
    for venue_name, code in VENUE_CODE_MAP.items():
        if venue_name in normalized:
            venue_code = code
            break
    return race_date, venue_code


def _parse_race_time_to_seconds(raw: str) -> float:
    """レースタイム文字列を秒へ変換する。"""
    value = normalize_fullwidth(raw).strip()
    if not value or value.replace(" ", "") == "..":
        return float("nan")
    match = re.match(r"^(\d+)\.(\d{2})\.(\d)$", value)
    if not match:
        return float("nan")
    minute, seconds, tenth = match.groups()
    return int(minute) * 60 + int(seconds) + int(tenth) / 10


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
    race_date, venue_code = _extract_file_context(text)
    current_race_no: int | None = None
    weather = ""
    wind_direction = ""
    wind_speed = float("nan")
    wave_height = float("nan")
    winning_technique = ""
    rows: list[dict[str, object]] = []

    lines = text.splitlines()
    for line_no, raw_line in enumerate(lines, start=1):
        line = normalize_fullwidth(raw_line)
        header_match = re.match(
            r"^\s*(\d+)R\s+.*?([晴曇雨雪])\s+風\s*([東西南北])\s*(\d+)m\s+波\s*(\d+)cm",
            line,
        )
        if header_match:
            try:
                current_race_no = int(header_match.group(1))
                weather = header_match.group(2)
                wind_direction = header_match.group(3)
                wind_speed = float(header_match.group(4))
                wave_height = float(header_match.group(5))
                winning_technique = ""
                if line_no + 2 < len(lines):
                    wt_match = re.search(r"(逃げ|まくり|差し|まくり差し|恵まれ)$", normalize_fullwidth(lines[line_no + 2]).strip())
                    if wt_match:
                        winning_technique = wt_match.group(1)
            except Exception as exc:  # noqa: BLE001
                LOGGER.exception("Failed to parse race header line %s: %s", line_no, exc)
            continue

        if not re.match(r"^\s+\d{2}\s+\d\s+\d{4}", line):
            continue

        if current_race_no is None:
            LOGGER.warning("Skip result line without race header at line %s", line_no)
            continue

        try:
            # 例: 01  1 3501 ... 50   12 6.89  1     0.08      1.49.7
            parts = re.split(r"\s+", line.strip())
            finish_position = _to_int(parts[0])
            lane = _to_int(parts[1])
            player_id = _to_int(parts[2])
            course_position = _to_int(parts[-3]) if len(parts) >= 3 else float("nan")
            start_timing = _to_float(parts[-2]) if len(parts) >= 2 else float("nan")
            race_time = _parse_race_time_to_seconds(parts[-1]) if parts else float("nan")

            rows.append(
                {
                    "race_date": race_date,
                    "venue_code": venue_code,
                    "race_number": current_race_no,
                    "lane": lane,
                    "player_id": player_id,
                    "finish_position": finish_position,
                    "race_time": race_time,
                    "course_position": course_position,
                    "start_timing": start_timing,
                    "winning_technique": winning_technique,
                    "weather": weather,
                    "wind_direction": wind_direction,
                    "wind_speed": wind_speed,
                    "wave_height": wave_height,
                    "temperature": float("nan"),
                    "water_temperature": float("nan"),
                }
            )
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
    race_date, venue_code = _extract_file_context(text)
    current_race_no: int | None = None
    payout_by_race: dict[int, dict[str, object]] = {}

    for line_no, raw_line in enumerate(text.splitlines(), start=1):
        line = normalize_fullwidth(raw_line)
        header_match = re.match(r"^\s*(\d+)R\s+", line)
        if header_match:
            current_race_no = int(header_match.group(1))
            payout_by_race[current_race_no] = {
                "race_date": race_date,
                "venue_code": venue_code,
                "race_number": current_race_no,
                "tansho_combo": "",
                "tansho_payout": float("nan"),
                "rentan2_combo": "",
                "rentan2_payout": float("nan"),
                "rentan3_combo": "",
                "rentan3_payout": float("nan"),
            }
            continue
        if current_race_no is None:
            continue
        try:
            tansho = re.search(r"単\s*勝\s+([0-9\-]+)\s+([0-9]+)", line)
            if tansho:
                payout_by_race[current_race_no]["tansho_combo"] = tansho.group(1)
                payout_by_race[current_race_no]["tansho_payout"] = int(tansho.group(2))

            rentan2 = re.search(r"2連単\s+([0-9\-]+)\s+([0-9]+)", line)
            if rentan2:
                payout_by_race[current_race_no]["rentan2_combo"] = rentan2.group(1)
                payout_by_race[current_race_no]["rentan2_payout"] = int(rentan2.group(2))

            rentan3 = re.search(r"3連単\s+([0-9\-]+)\s+([0-9]+)", line)
            if rentan3:
                payout_by_race[current_race_no]["rentan3_combo"] = rentan3.group(1)
                payout_by_race[current_race_no]["rentan3_payout"] = int(rentan3.group(2))
        except Exception as exc:  # noqa: BLE001
            LOGGER.exception("Failed to parse payout line %s: %s", line_no, exc)
    rows = list(payout_by_race.values())
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

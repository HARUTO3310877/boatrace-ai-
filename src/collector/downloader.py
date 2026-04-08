"""BOAT RACE 公式サイトの LZH データをダウンロードするモジュール。"""

from __future__ import annotations

import argparse
import logging
import time
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Iterator

import requests

LOGGER = logging.getLogger(__name__)
BASE_URLS = {
    "bangumi": "https://www1.mbrace.or.jp/od2/B/{yyyymm}/b{yymmdd}.lzh",
    "results": "https://www1.mbrace.or.jp/od2/K/{yyyymm}/k{yymmdd}.lzh",
}


def iter_dates(start_date: date, end_date: date) -> Iterator[date]:
    """開始日から終了日までの日付を列挙する。

    Args:
        start_date: 開始日。
        end_date: 終了日。

    Yields:
        date: start_date から end_date までの日付。
    """
    current = start_date
    while current <= end_date:
        yield current
        current += timedelta(days=1)


def build_download_url(target_date: date, data_type: str) -> str:
    """日付とデータ種別からダウンロード URL を生成する。

    Args:
        target_date: 対象日付。
        data_type: ``bangumi`` または ``results``。

    Returns:
        生成されたダウンロード URL。

    Raises:
        ValueError: ``data_type`` が不正な場合。
    """
    if data_type not in BASE_URLS:
        raise ValueError("data_type must be either 'bangumi' or 'results'.")

    return BASE_URLS[data_type].format(
        yyyymm=target_date.strftime("%Y%m"),
        yymmdd=target_date.strftime("%y%m%d"),
    )


def download_files(start_date: str, end_date: str, data_type: str, output_dir: str | Path) -> None:
    """指定期間の LZH ファイルを一括ダウンロードする。

    Args:
        start_date: 開始日 (YYYY-MM-DD)。
        end_date: 終了日 (YYYY-MM-DD)。
        data_type: ``bangumi``（番組表）または ``results``（競走成績）。
        output_dir: 保存先ディレクトリ。

    Raises:
        ValueError: 日付形式、不正な日付範囲、または ``data_type`` が不正な場合。
    """
    if data_type not in BASE_URLS:
        raise ValueError("data_type must be either 'bangumi' or 'results'.")

    try:
        start = datetime.strptime(start_date, "%Y-%m-%d").date()
        end = datetime.strptime(end_date, "%Y-%m-%d").date()
    except ValueError as exc:
        raise ValueError("start_date and end_date must be in YYYY-MM-DD format.") from exc

    if start > end:
        raise ValueError("start_date must be earlier than or equal to end_date.")

    target_dir = Path(output_dir)
    target_dir.mkdir(parents=True, exist_ok=True)

    for target_date in iter_dates(start, end):
        file_name = f"{'b' if data_type == 'bangumi' else 'k'}{target_date.strftime('%y%m%d')}.lzh"
        destination = target_dir / file_name

        if destination.exists():
            LOGGER.info("Skip existing file: %s", destination)
            continue

        url = build_download_url(target_date, data_type)

        for attempt in range(1, 4):
            try:
                LOGGER.info("Downloading: %s", url)
                response = requests.get(url, timeout=30)

                if response.status_code == 404:
                    LOGGER.info("No race data (404): %s", target_date)
                    break

                response.raise_for_status()
                destination.write_bytes(response.content)
                LOGGER.info("Saved: %s", destination)
                break
            except requests.HTTPError as exc:
                if attempt == 3:
                    LOGGER.error("HTTP error after retries (%s): %s", url, exc)
                    break
                LOGGER.warning("HTTP error retry %d/3: %s", attempt, exc)
                time.sleep(2)
            except requests.RequestException as exc:
                if attempt == 3:
                    LOGGER.error("Request failed after retries (%s): %s", url, exc)
                    break
                LOGGER.warning("Request retry %d/3 due to error: %s", attempt, exc)
                time.sleep(2)

        time.sleep(1)


def main() -> None:
    """CLI エントリーポイント。"""
    parser = argparse.ArgumentParser(description="BOAT RACE LZH downloader")
    parser.add_argument("--start", required=True, help="開始日 (YYYY-MM-DD)")
    parser.add_argument("--end", required=True, help="終了日 (YYYY-MM-DD)")
    parser.add_argument("--type", required=True, choices=["bangumi", "results"], help="データ種別")
    parser.add_argument(
        "--output-dir",
        default=None,
        help="保存先ディレクトリ（省略時: data/raw/<type>）",
    )
    args = parser.parse_args()

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s - %(message)s",
    )

    output_dir = Path(args.output_dir) if args.output_dir else Path("data/raw") / args.type
    download_files(
        start_date=args.start,
        end_date=args.end,
        data_type=args.type,
        output_dir=output_dir,
    )


if __name__ == "__main__":
    main()

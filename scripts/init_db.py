"""CLI から SQLite DB を初期化するスクリプト。"""

from __future__ import annotations

import argparse

from src.database.loader import init_db


def main() -> None:
    """スクリプトエントリーポイント。"""
    parser = argparse.ArgumentParser(description="Initialize boatrace SQLite database")
    parser.add_argument("--db-path", required=True, help="SQLite DB path")
    args = parser.parse_args()

    init_db(args.db_path)


if __name__ == "__main__":
    main()

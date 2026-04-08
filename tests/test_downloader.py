"""Tests for src.collector.downloader."""

from datetime import date
from pathlib import Path
from unittest.mock import Mock, patch

import pytest
import requests

from src.collector.downloader import build_download_url, download_files


@patch("src.collector.downloader.time.sleep", return_value=None)
@patch("src.collector.downloader.requests.get")
def test_build_download_url_is_correct(mock_get: Mock, _mock_sleep: Mock) -> None:
    """URL 生成が仕様どおりであることを確認する。"""
    bangumi_url = build_download_url(target_date=date(2025, 12, 31), data_type="bangumi")
    result_url = build_download_url(target_date=date(2025, 12, 31), data_type="results")

    assert bangumi_url == "https://www1.mbrace.or.jp/od2/B/202512/b251231.lzh"
    assert result_url == "https://www1.mbrace.or.jp/od2/K/202512/k251231.lzh"
    mock_get.assert_not_called()


@patch("src.collector.downloader.time.sleep", return_value=None)
@patch("src.collector.downloader.requests.get")
def test_existing_file_is_skipped(mock_get: Mock, _mock_sleep: Mock, tmp_path: Path) -> None:
    """既存ファイルがある場合はダウンロードをスキップする。"""
    existing = tmp_path / "b250101.lzh"
    existing.write_bytes(b"already exists")

    download_files(
        start_date="2025-01-01",
        end_date="2025-01-01",
        data_type="bangumi",
        output_dir=tmp_path,
    )

    mock_get.assert_not_called()


def test_invalid_date_range_raises_value_error(tmp_path: Path) -> None:
    """開始日が終了日より後ろの場合に ValueError を投げる。"""
    with pytest.raises(ValueError, match="start_date must be earlier"):
        download_files(
            start_date="2025-01-02",
            end_date="2025-01-01",
            data_type="results",
            output_dir=tmp_path,
        )


@patch("src.collector.downloader.time.sleep", return_value=None)
@patch("src.collector.downloader.requests.get")
def test_download_uses_requests_mock(mock_get: Mock, _mock_sleep: Mock, tmp_path: Path) -> None:
    """HTTP リクエストがモックで処理されることを確認する。"""
    response = Mock()
    response.status_code = 200
    response.content = b"dummy"
    response.raise_for_status = Mock()
    mock_get.return_value = response

    download_files(
        start_date="2025-01-01",
        end_date="2025-01-01",
        data_type="results",
        output_dir=tmp_path,
    )

    saved = tmp_path / "k250101.lzh"
    assert saved.exists()
    assert saved.read_bytes() == b"dummy"
    mock_get.assert_called_once_with("https://www1.mbrace.or.jp/od2/K/202501/k250101.lzh", timeout=30)


@patch("src.collector.downloader.time.sleep", return_value=None)
@patch("src.collector.downloader.requests.get")
def test_retry_on_http_error_then_success(mock_get: Mock, _mock_sleep: Mock, tmp_path: Path) -> None:
    """HTTP エラー時にリトライし、成功したら保存する。"""
    error_response = Mock()
    error_response.status_code = 500
    error_response.raise_for_status.side_effect = requests.HTTPError("500 error")

    success_response = Mock()
    success_response.status_code = 200
    success_response.content = b"ok"
    success_response.raise_for_status = Mock()

    mock_get.side_effect = [error_response, success_response]

    download_files(
        start_date="2025-01-02",
        end_date="2025-01-02",
        data_type="results",
        output_dir=tmp_path,
    )

    assert (tmp_path / "k250102.lzh").read_bytes() == b"ok"
    assert mock_get.call_count == 2

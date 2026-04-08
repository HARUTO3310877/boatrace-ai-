"""SQLite テーブル定義。"""

from __future__ import annotations

from datetime import date

from sqlalchemy import Date, Float, ForeignKey, Integer, String
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    """Declarative Base。"""


class Race(Base):
    """レース情報テーブル。"""

    __tablename__ = "races"

    race_id: Mapped[str] = mapped_column(String, primary_key=True)
    race_date: Mapped[date] = mapped_column(Date, nullable=False)
    venue_code: Mapped[int | None] = mapped_column(Integer)
    race_number: Mapped[int | None] = mapped_column(Integer)
    weather: Mapped[str | None] = mapped_column(String)
    wind_direction: Mapped[str | None] = mapped_column(String)
    wind_speed: Mapped[float | None] = mapped_column(Float)
    wave_height: Mapped[float | None] = mapped_column(Float)
    temperature: Mapped[float | None] = mapped_column(Float)
    water_temperature: Mapped[float | None] = mapped_column(Float)


class Entry(Base):
    """番組表エントリテーブル。"""

    __tablename__ = "entries"

    race_id: Mapped[str] = mapped_column(ForeignKey("races.race_id"), primary_key=True)
    lane: Mapped[int] = mapped_column(Integer, primary_key=True)
    player_id: Mapped[int | None] = mapped_column(Integer)
    player_name: Mapped[str | None] = mapped_column(String)
    age: Mapped[int | None] = mapped_column(Integer)
    branch: Mapped[str | None] = mapped_column(String)
    weight: Mapped[float | None] = mapped_column(Float)
    class_rank: Mapped[str | None] = mapped_column(String)
    win_rate_national: Mapped[float | None] = mapped_column(Float)
    top2_rate_national: Mapped[float | None] = mapped_column(Float)
    win_rate_local: Mapped[float | None] = mapped_column(Float)
    top2_rate_local: Mapped[float | None] = mapped_column(Float)
    motor_no: Mapped[int | None] = mapped_column(Integer)
    motor_top2_rate: Mapped[float | None] = mapped_column(Float)
    boat_no: Mapped[int | None] = mapped_column(Integer)
    boat_top2_rate: Mapped[float | None] = mapped_column(Float)


class Result(Base):
    """レース結果テーブル。"""

    __tablename__ = "results"

    race_id: Mapped[str] = mapped_column(ForeignKey("races.race_id"), primary_key=True)
    lane: Mapped[int] = mapped_column(Integer, primary_key=True)
    finish_position: Mapped[int | None] = mapped_column(Integer)
    course_position: Mapped[int | None] = mapped_column(Integer)
    start_timing: Mapped[float | None] = mapped_column(Float)
    race_time: Mapped[float | None] = mapped_column(Float)
    winning_technique: Mapped[str | None] = mapped_column(String)


class Payout(Base):
    """払戻金テーブル。"""

    __tablename__ = "payouts"

    race_id: Mapped[str] = mapped_column(ForeignKey("races.race_id"), primary_key=True)
    tansho_combo: Mapped[str | None] = mapped_column(String)
    tansho_payout: Mapped[int | None] = mapped_column(Integer)
    rentan2_combo: Mapped[str | None] = mapped_column(String)
    rentan2_payout: Mapped[int | None] = mapped_column(Integer)
    rentan3_combo: Mapped[str | None] = mapped_column(String)
    rentan3_payout: Mapped[int | None] = mapped_column(Integer)

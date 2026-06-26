"""状态管理模块 — JSON 文件持久化 + 限流逻辑 + 电量历史追踪。"""

import json
from dataclasses import dataclass, asdict
from datetime import date, datetime
from pathlib import Path


@dataclass
class State:
    low_power_count: int = 0
    error_count: int = 0
    last_daily_report_date: str = ""  # "YYYY-MM-DD"
    last_power_value: float = 0.0
    last_low_power_notified_value: float = -1.0
    daily_start_power: float = 0.0
    daily_start_date: str = ""
    last_reading_time: str = ""


class StateManager:
    def __init__(self, filepath: str = "power_alert_state.json"):
        self.filepath = Path(filepath)
        self.state = self._load()

    def _load(self) -> State:
        if not self.filepath.exists():
            return State()
        try:
            data = json.loads(self.filepath.read_text(encoding="utf-8"))
            valid_keys = set(State.__dataclass_fields__.keys())
            return State(**{k: v for k, v in data.items() if k in valid_keys})
        except (json.JSONDecodeError, TypeError):
            return State()

    def _save(self):
        self.filepath.write_text(
            json.dumps(asdict(self.state), ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

    # ── 电量记录与消耗计算 ──

    def record_power(self, power: float):
        now = datetime.now()
        today = date.today().isoformat()

        # 新的一天，重置日基准
        if self.state.daily_start_date != today or self.state.daily_start_power == 0.0:
            self.state.daily_start_power = power
            self.state.daily_start_date = today

        self.state.last_power_value = power
        self.state.last_reading_time = now.isoformat()
        self._save()

    def get_consumption_4h(self) -> float | None:
        """返回自上次读数以来的消耗量（度），首次运行返回 None。"""
        prev = self.state.last_power_value
        cur = self.state.last_power_value
        # We need previous vs current; caller gives us the current value
        # This is called before record_power, so last_power_value is the previous
        if self.state.last_power_value == 0.0 and self.state.last_reading_time == "":
            return None
        # Will be calculated by caller with current value
        return None  # caller handles the math

    def get_prev_power(self) -> float:
        return self.state.last_power_value

    def get_daily_start_power(self) -> float:
        return self.state.daily_start_power

    def get_daily_start_date(self) -> str:
        return self.state.daily_start_date

    def has_previous_reading(self) -> bool:
        return self.state.last_reading_time != ""

    # ── 低电量逻辑 ──

    def should_send_low_power_alert(self, max_count: int) -> bool:
        return self.state.low_power_count < max_count

    def record_low_power_alert(self, power: float):
        self.state.low_power_count += 1
        self.state.last_low_power_notified_value = power
        self._save()

    def reset_low_power_if_recovered(self, current_power: float, threshold: float):
        if (
            current_power >= threshold
            and self.state.low_power_count > 0
            and self.state.last_low_power_notified_value < threshold
        ):
            self.state.low_power_count = 0
            self.state.last_low_power_notified_value = -1.0
            self._save()

    # ── 错误逻辑 ──

    def should_send_error_alert(self, max_count: int) -> bool:
        return self.state.error_count < max_count

    def record_error_alert(self):
        self.state.error_count += 1
        self._save()

    def reset_error_count(self):
        if self.state.error_count > 0:
            self.state.error_count = 0
            self._save()

    # ── 日报逻辑 ──

    def should_send_daily_report(self, report_hour: int) -> bool:
        today = date.today().isoformat()
        now = datetime.now()
        if now.hour < report_hour:
            return False
        return self.state.last_daily_report_date != today

    def record_daily_report(self):
        self.state.last_daily_report_date = date.today().isoformat()
        self._save()

"""配置加载模块 — 优先级：环境变量 > 本地 config.json > 默认值。"""

import json
import os
from pathlib import Path

# ── 默认值 ──
DEFAULTS = {
    "api_url": "https://mcard.sdu.edu.cn/charge/feeitem/getThirdData",
    "api_type": "IEC",
    "api_level": "3",
    "api_feeitemid": "410",
    "api_timeout": 10,
    "low_power_threshold": 5.0,
    "max_alert_count": 3,
    "daily_report_hour": 8,
    "state_file": "power_alert_state.json",
    "campus_name": "青岛校区",
    "building_name": "",
    "room": "",
}
CONFIG_FILE = Path("config.json")

# ── 本地配置文件缓存 ──
_local_config: dict | None = None


def _load_local_config() -> dict:
    global _local_config
    if _local_config is not None:
        return _local_config
    if CONFIG_FILE.exists():
        try:
            _local_config = json.loads(CONFIG_FILE.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            _local_config = {}
    else:
        _local_config = {}
    return _local_config


def reload():
    """重新加载本地配置文件（GUI 保存后调用）。"""
    global _local_config
    _local_config = None


ENV_MAP = {
    "synjones_auth": "SYNJONES_AUTH",
    "feishu_webhook_url": "FEISHU_WEBHOOK_URL",
    "campus_param": "CAMPUS_PARAM",
    "building_param": "BUILDING_PARAM",
    "room": "ROOM",
    "low_power_threshold": "LOW_POWER_THRESHOLD",
    "max_alert_count": "MAX_ALERT_COUNT",
    "daily_report_hour": "DAILY_REPORT_HOUR",
    "campus_name": "CAMPUS_NAME",
    "building_name": "BUILDING_NAME",
}


def get(key: str) -> str:
    # 1. 环境变量
    env_name = ENV_MAP.get(key)
    if env_name:
        val = os.environ.get(env_name)
        if val is not None:
            return val

    # 2. 本地 config.json
    local = _load_local_config()
    if key in local:
        return str(local[key])

    # 3. 默认值
    return str(DEFAULTS.get(key, ""))


def get_float(key: str) -> float:
    return float(get(key))


def get_int(key: str) -> int:
    return int(float(get(key)))


def get_api_url() -> str:
    return str(DEFAULTS["api_url"])


def get_api_payload() -> dict:
    return {
        "type": DEFAULTS["api_type"],
        "level": DEFAULTS["api_level"],
        "feeitemid": DEFAULTS["api_feeitemid"],
        "campus": get("campus_param"),
        "building": get("building_param"),
        "room": get("room"),
    }


def get_request_headers() -> dict:
    return {
        "Synjones-Auth": get("synjones_auth"),
    }

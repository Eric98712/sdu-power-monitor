"""山大电控 API 客户端 — 查询宿舍剩余电量。"""

import re

import requests
from src import config


class ApiError(Exception):
    """API 调用错误。"""

    def __init__(self, message: str, status_code: int | None = None):
        super().__init__(message)
        self.status_code = status_code


def fetch_power() -> dict:
    """查询电量，返回原始 JSON。失败时抛出 ApiError。"""
    url = config.get_api_url()
    headers = config.get_request_headers()
    payload = config.get_api_payload()
    timeout = config.DEFAULTS["api_timeout"]

    try:
        resp = requests.post(url, data=payload, headers=headers, timeout=timeout)
    except requests.Timeout:
        raise ApiError(f"请求超时 ({timeout}s)")
    except requests.ConnectionError:
        raise ApiError("网络连接失败，无法访问电控接口")

    if resp.status_code == 401:
        raise ApiError("Token 已过期 (HTTP 401)，请更新 SYNJONES_AUTH", 401)
    if resp.status_code != 200:
        body = resp.text[:200]
        raise ApiError(f"HTTP {resp.status_code}: {body}", resp.status_code)

    data = resp.json()
    if not isinstance(data, dict):
        raise ApiError(f"接口返回格式异常: {type(data).__name__}")

    if data.get("code") != 200:
        raise ApiError(f"接口返回错误: {data.get('msg', '未知错误')}")

    return data


def parse_power(data: dict) -> float:
    """从 API 返回 JSON 中提取剩余电量（度）。"""
    show_data = data.get("map", {}).get("showData", {})
    info = show_data.get("信息", "")
    if not info:
        raise ApiError("返回数据中缺少电量信息字段")

    match = re.search(r"[\d.]+", str(info))
    if not match:
        raise ApiError(f"无法从信息字段解析电量: {info}")
    return float(match.group())

"""飞书通知模块 — 通过自定义机器人 Webhook 发送消息。"""

import json
from datetime import datetime

import requests


class NotifyError(Exception):
    """通知发送失败。"""


def _send_card(title: str, color: str, fields: list[tuple[str, str]], webhook_url: str):
    """发送飞书卡片消息。

    Args:
        title: 卡片标题
        color: 标题颜色 (red/yellow/blue)
        fields: [(label, value), ...] 键值对列表
        webhook_url: 飞书机器人 Webhook 地址
    """
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    field_blocks = []
    for label, value in fields:
        field_blocks.append(
            {"tag": "div", "text": {"tag": "lark_md", "content": f"**{label}**：{value}"}}
        )

    card = {
        "msg_type": "interactive",
        "card": {
            "header": {
                "title": {"tag": "plain_text", "content": title},
                "template": color,
            },
            "elements": [
                *field_blocks,
                {"tag": "hr"},
                {
                    "tag": "div",
                    "text": {
                        "tag": "lark_md",
                        "content": f"⏰ 检测时间：{now}",
                    },
                },
            ],
        },
    }

    try:
        resp = requests.post(webhook_url, json=card, timeout=10)
        if resp.status_code != 200:
            raise NotifyError(f"飞书返回 HTTP {resp.status_code}: {resp.text[:200]}")
        result = resp.json()
        if result.get("code") != 0:
            raise NotifyError(f"飞书返回错误 code={result.get('code')}: {result.get('msg', '')}")
    except requests.RequestException as e:
        raise NotifyError(f"飞书请求失败: {e}")


def send_low_power_alert(
    campus: str,
    building: str,
    room: str,
    power: float,
    threshold: float,
    count: int,
    max_count: int,
    webhook_url: str,
):
    """发送低电量告警。"""
    _send_card(
        title=f"⚠️ 低电量预警 [{count}/{max_count}]",
        color="red",
        fields=[
            ("📍 位置", f"{campus} {building} {room}"),
            ("🔋 当前剩余电量", f"{power:.2f} 度"),
            ("🚨 预警阈值", f"{threshold:.1f} 度"),
            ("📧 警告次数", f"{count}/{max_count}（电量恢复前最多发送 {max_count} 次）"),
        ],
        webhook_url=webhook_url,
    )


def send_daily_report(
    campus: str,
    building: str,
    room: str,
    power: float,
    daily_usage: float,
    webhook_url: str,
):
    """发送每日电量日报。"""
    days_left = power / daily_usage if daily_usage > 0 else float("inf")
    days_text = f"{days_left:.1f} 天" if days_left != float("inf") else "无法估算"

    _send_card(
        title="📊 电量日报",
        color="blue",
        fields=[
            ("📍 位置", f"{campus} {building} {room}"),
            ("🔋 当前剩余电量", f"{power:.2f} 度"),
            ("📈 预计可用", f"{days_text}（按日均 {daily_usage} 度估算）"),
        ],
        webhook_url=webhook_url,
    )


def send_error_alert(
    campus: str,
    building: str,
    room: str,
    error_msg: str,
    count: int,
    max_count: int,
    webhook_url: str,
):
    """发送查询异常告警。"""
    _send_card(
        title=f"❌ 电量查询失败 [{count}/{max_count}]",
        color="yellow",
        fields=[
            ("📍 位置", f"{campus} {building} {room}"),
            ("❌ 错误信息", error_msg),
            ("📧 警告次数", f"{count}/{max_count}（恢复正常前最多发送 {max_count} 次）"),
        ],
        webhook_url=webhook_url,
    )

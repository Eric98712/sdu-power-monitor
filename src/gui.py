"""Web GUI 配置界面 — Flask 本地服务，浏览器中打开配置页面。

Usage:
    python -m src.gui       # 启动配置页面
    python -m src.gui --run # 启动后直接运行主程序
"""

import json
import sys
import webbrowser
from pathlib import Path

from flask import Flask, request, jsonify, send_file
import requests

from src import config

GUI_HTML = Path(__file__).parent / "gui.html"

app = Flask(__name__)


@app.route("/")
def index():
    return send_file(str(GUI_HTML))


@app.route("/api/load")
def api_load():
    """返回当前配置（config.json 或默认值）。"""
    config.reload()
    return jsonify(
        {
            "campus_name": config.get("campus_name"),
            "campus_param": config.get("campus_param"),
            "building_name": config.get("building_name"),
            "building_param": config.get("building_param"),
            "room": config.get("room"),
            "token": config.get("synjones_auth"),
            "feishu_webhook_url": config.get("feishu_webhook_url"),
            "threshold": config.get("low_power_threshold"),
            "max_count": config.get("max_alert_count"),
        }
    )


@app.route("/api/save", methods=["POST"])
def api_save():
    """保存配置到 config.json。"""
    data = request.get_json()
    saved = {
        "campus_name": data.get("campus_name", "").strip(),
        "campus_param": data.get("campus_param", "").strip(),
        "building_name": data.get("building_name", "").strip(),
        "building_param": data.get("building_param", "").strip(),
        "room": data.get("room", "").strip(),
        "synjones_auth": data.get("token", "").strip(),
        "feishu_webhook_url": data.get("feishu_webhook_url", "").strip(),
        "low_power_threshold": data.get("threshold", "5.0"),
        "max_alert_count": data.get("max_count", "3"),
    }
    config.CONFIG_FILE.write_text(
        json.dumps(saved, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    config.reload()
    return jsonify({"ok": True})


@app.route("/api/test", methods=["POST"])
def api_test():
    """测试 API 连接。"""
    data = request.get_json()
    token = data.get("token", "").strip()
    campus_param = data.get("campus_param", "").strip()
    building_param = data.get("building_param", "").strip()
    room = data.get("room", "").strip()

    if not token:
        return jsonify({"ok": False, "error": "Token 不能为空"})
    if not campus_param or not building_param or not room:
        return jsonify({"ok": False, "error": "校区参数、楼栋参数、房间号不能为空"})

    url = config.DEFAULTS["api_url"]
    headers = {"Synjones-Auth": token}
    payload = {
        "type": config.DEFAULTS["api_type"],
        "level": config.DEFAULTS["api_level"],
        "feeitemid": config.DEFAULTS["api_feeitemid"],
        "campus": campus_param,
        "building": building_param,
        "room": room,
    }

    try:
        resp = requests.post(url, data=payload, headers=headers, timeout=10)
        if resp.status_code == 401:
            return jsonify({"ok": False, "error": "Token 已过期 (HTTP 401)，请重新获取"})
        if resp.status_code != 200:
            return jsonify(
                {"ok": False, "error": f"HTTP {resp.status_code}: {resp.text[:200]}"}
            )
        data = resp.json()
        from src.api_client import parse_power, ApiError
        try:
            power = parse_power(data)
            return jsonify({"ok": True, "power": power})
        except ApiError as e:
            return jsonify(
                {"ok": False, "error": f"解析失败: {e}，原始返回: {json.dumps(data, ensure_ascii=False)}"}
            )
    except requests.Timeout:
        return jsonify({"ok": False, "error": "请求超时"})
    except requests.ConnectionError:
        return jsonify({"ok": False, "error": "网络连接失败"})
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)})


@app.route("/api/test-feishu", methods=["POST"])
def api_test_feishu():
    """测试飞书 Webhook。"""
    data = request.get_json()
    webhook_url = data.get("webhook_url", "").strip()
    if not webhook_url:
        return jsonify({"ok": False, "error": "Webhook URL 不能为空"})

    card = {
        "msg_type": "interactive",
        "card": {
            "header": {
                "title": {"tag": "plain_text", "content": "🧪 飞书连接测试"},
                "template": "blue",
            },
            "elements": [
                {
                    "tag": "div",
                    "text": {"tag": "lark_md", "content": "✅ 飞书机器人连接成功！\n\n如果你收到这条消息，说明 Webhook 配置正确，后续电费告警将正常推送。"},
                }
            ],
        },
    }
    try:
        resp = requests.post(webhook_url, json=card, timeout=10)
        if resp.status_code != 200:
            return jsonify({"ok": False, "error": f"HTTP {resp.status_code}: {resp.text[:200]}"})
        result = resp.json()
        if result.get("code") != 0:
            return jsonify({"ok": False, "error": f"飞书返回: code={result.get('code')} {result.get('msg','')}"})
        return jsonify({"ok": True})
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)})


def main():
    host = "127.0.0.1"
    port = 18920

    if "--run" in sys.argv:
        webbrowser.open(f"http://{host}:{port}")
        app.run(host=host, port=port, debug=False)
    else:
        print(f"电费预警配置面板: http://{host}:{port}")
        print("按 Ctrl+C 退出")
        webbrowser.open(f"http://{host}:{port}")
        app.run(host=host, port=port, debug=False)


if __name__ == "__main__":
    main()

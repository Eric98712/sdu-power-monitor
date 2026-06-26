"""电费预警系统主入口 — 查询电量 + 决策 + 通知。

通过 GitHub Actions 定时调用，也可本地手动运行。
"""

import sys
from datetime import datetime

from src import config
from src.api_client import fetch_power, parse_power, ApiError
from src.notifier import (
    send_low_power_alert,
    send_daily_report,
    send_error_alert,
    NotifyError,
)
from src.state_manager import StateManager

DAILY_USAGE_ESTIMATE = 3.0  # 日均用电量估算（度）


def run():
    state = StateManager(config.get("state_file"))
    webhook_url = config.get("feishu_webhook_url")
    if not webhook_url:
        print("[FAIL] FEISHU_WEBHOOK_URL not configured")
        sys.exit(1)

    threshold = config.get_float("low_power_threshold")
    max_count = config.get_int("max_alert_count")
    report_hour = config.get_int("daily_report_hour")
    campus = config.get("campus_name")
    building = config.get("building_name")
    room = config.get("room")

    print("=" * 50)
    print("[PowerMonitor] Starting...")
    print(f"  Location: {campus} {building} {room}")
    print("=" * 50)

    # 1. Query power
    try:
        data = fetch_power()
        power = parse_power(data)
        print(f"[OK] Power: {power:.2f} kWh")
        state.reset_error_count()
    except ApiError as e:
        print(f"[FAIL] Query failed: {e}")
        if state.should_send_error_alert(max_count):
            try:
                send_error_alert(
                    campus, building, room, str(e),
                    state.state.error_count + 1, max_count, webhook_url,
                )
                state.record_error_alert()
                print(f"[OK] Error alert sent ({state.state.error_count}/{max_count})")
            except NotifyError as ne:
                print(f"[FAIL] Feishu error: {ne}")
        else:
            print(f"[SKIP] Error alert limit reached ({state.state.error_count}/{max_count})")
        return

    state.record_power(power)

    # 2. Low power check
    if power < threshold:
        print(f"[WARN] Power low ({power:.2f} < {threshold})")
        if state.should_send_low_power_alert(max_count):
            try:
                send_low_power_alert(
                    campus, building, room, power, threshold,
                    state.state.low_power_count + 1, max_count, webhook_url,
                )
                state.record_low_power_alert(power)
                print(f"[OK] Low power alert sent ({state.state.low_power_count}/{max_count})")
            except NotifyError as e:
                print(f"[FAIL] Feishu error: {e}")
        else:
            print(f"[SKIP] Alert limit reached ({state.state.low_power_count}/{max_count})")
    else:
        print(f"[OK] Power sufficient ({power:.2f} kWh)")
        state.reset_low_power_if_recovered(power, threshold)

        # 3. Daily report
        if state.should_send_daily_report(report_hour):
            try:
                send_daily_report(campus, building, room, power, DAILY_USAGE_ESTIMATE, webhook_url)
                state.record_daily_report()
                print("[OK] Daily report sent")
            except NotifyError as e:
                print(f"[FAIL] Feishu error: {e}")

    print("[DONE]")
    print("=" * 50)


if __name__ == "__main__":
    run()

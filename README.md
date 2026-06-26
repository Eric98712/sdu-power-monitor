# 山东大学宿舍电费预警系统

自动监控宿舍电量，低电量时通过**飞书机器人**推送告警，基于 GitHub Actions 定时运行。

## 功能

- **低电量告警**：电量低于阈值时通过飞书推送告警
- **每日日报**：电量充足时每天早上发送电量报告
- **智能限流**：同一状态最多发送 3 次告警，恢复后自动重置
- **异常通知**：API 查询失败时推送通知

## 工作原理

```
GitHub Actions (每4小时)
  → Python 脚本调用山大电控 API 查询电量
  → 判断电量状态
  → 通过飞书 Webhook 推送通知
  → 状态持久化到 Git 仓库
```

## 快速开始

### 1. 获取 API Token

参考博客文章：[山东大学宿舍电费不足预警脚本](https://www.orangehome.cc/2026/03/19/山大学宿舍电费不足预警脚本/)

简略步骤：
1. 浏览器登录 [校园卡综合服务平台](https://mcard.sdu.edu.cn/plat-pc/businesslobby)
2. F12 打开开发者工具 → Network 标签
3. 进入"青岛电控"页面，点击查询
4. 找到 `getThirdData` 请求，复制 `Synjones-Auth`（以 `bearer ` 开头）
5. 同时记录 campus、building、room 参数

### 2. 创建飞书机器人

1. 打开飞书，进入目标群聊
2. 群设置 → 群机器人 → 添加自定义机器人
3. 复制 Webhook URL（格式：`https://open.feishu.cn/open-apis/bot/v2/hook/xxx`）

### 3. 配置 GitHub Secrets

在仓库 Settings → Secrets and variables → Actions → New repository secret：

| Secret | 说明 | 示例 |
|--------|------|------|
| `SYNJONES_AUTH` | API 认证 Token | `bearer eyJ...` |
| `FEISHU_WEBHOOK_URL` | 飞书机器人 Webhook | `https://open.feishu.cn/...` |
| `CAMPUS_PARAM` | 校区接口参数 | `青岛校区&青岛校区` |
| `BUILDING_PARAM` | 楼栋接口参数 | `1503975832&凤凰居1号楼` |
| `ROOM` | 房间号 | `b111` |
| `CAMPUS_NAME` | 校区显示名称 | `青岛校区` |
| `BUILDING_NAME` | 楼栋显示名称 | `凤凰居1号楼` |
| `LOW_POWER_THRESHOLD` | 预警阈值（度） | `5.0` |
| `MAX_ALERT_COUNT` | 最大告警次数 | `3` |

### 4. GUI 配置面板（推荐）

一键启动 Web 配置界面，在浏览器中可视化填写所有参数：

```bash
pip install -r requirements.txt
python -m src.gui
```

浏览器会自动打开配置面板，你可以：
- 填写宿舍信息、Token、飞书 Webhook
- 点击「测试 API 连接」验证参数是否正确
- 点击「测试飞书连接」确认通知通道正常
- 点击「保存配置」将所有参数保存到 config.json

### 6. 本地命令行测试

```bash
# 通过 GUI 保存配置后，直接运行
python -m src.main

# 或者通过环境变量覆盖
export SYNJONES_AUTH="bearer YOUR_TOKEN"
export FEISHU_WEBHOOK_URL="https://open.feishu.cn/..."
python -m src.main
```

### 7. GitHub Actions 验证

- 推送代码到 GitHub 后，在 Actions 标签手动触发 `电费监控` workflow
- 检查飞书群是否收到通知
- 每 4 小时自动运行一次

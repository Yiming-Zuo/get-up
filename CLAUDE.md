# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## 项目概述

这是一个自动化起床打卡系统，通过 GitHub Actions 在特定时间段内记录起床时间到 GitHub Issue，并可选地发送消息到 Telegram。

## 核心架构

- **get_up.py**: 主脚本，负责：
  - 检查今天是否已经打卡（通过 Issue #12 的评论）
  - 生成包含起床时间和古诗句的打卡消息
  - 在早起时间段（4:00-10:00）内创建 GitHub Issue 评论
  - 可选发送消息到 Telegram

- **GitHub Actions 工作流**: 通过手动触发（workflow_dispatch）运行打卡脚本

## 常用命令

```bash
# 安装依赖
python -m venv venv
source venv/bin/activate  # Linux/Mac
pip install -r requirements.txt

# 本地测试运行（需要提供 GitHub Token 和仓库名）
python get_up.py <github_token> <repo_name> [--weather_message "天气信息"] [--tele_token <token>] [--tele_chat_id <chat_id>]

# 手动触发 GitHub Actions
# 在 GitHub 仓库页面 -> Actions -> GET UP -> Run workflow
```

## 关键配置

- **Issue 编号**: GET_UP_ISSUE_NUMBER = 1（硬编码在 get_up.py 中）
- **时区**: Asia/Shanghai
- **早起时间段**: 4:00-10:00
- **依赖的 API**: https://v1.jinrishici.com/all（获取每日古诗句）

## 必需的 GitHub Secrets

- `G_T`: GitHub Token，用于访问和评论 Issue
- `TELE_TOKEN`: （可选）Telegram Bot Token
- `TELE_CHAT_ID`: （可选）Telegram Chat ID
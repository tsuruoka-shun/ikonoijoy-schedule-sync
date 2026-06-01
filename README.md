# ikonoijoy-schedule-sync

---

## 📜 目次
1. [概要](#-概要)
2. [使用技術](#-使用技術)
3. [ディレクトリ構成](#-ディレクトリ構成)
4. [Gitルール](#-Gitルール)
    - [ブランチ命名規則](#-ブランチ命名規則)
    - [コミットメッセージ規則](#-コミットメッセージ規則)


## 💡 概要

各グループの公式スケジュールページから、スクレイピングをしてスケジュールを取得します。  
取得したスケジュールをもとに、個人Googleカレンダーに予定を同期（作成、更新、削除）をします。
> 対象サイト
> - https://equal-love.jp/schedule
> - https://not-equal-me.jp/schedule
> - https://nearly-equal-joy.jp/schedule

---

## 🛠️ 使用技術

### Python
- Python 3.13

### Pythonプロジェクト管理
- uv

### 使用パッケージ
- requests
- beautifulsoup4
- google-api-python-client
- google-auth
- google-cloud-secret-manager

### Google Cloudサービス
- Calendar API
- Cloud Run
- Cloud Secret Manager
- Cloud Scheduler

---

## 📁 ディレクトリ構成

```
.
├── .github/
│   ├── workflows/
│   │   ├── branch_restrictions.yaml
│   │   └── ci.yaml
│   └── pull_request_template.md
├── scraper/
│   ├── __init__.py
│   └── schedule.py                    # スクレイピング
├── sync/
│   ├── __init__.py
│   └── google_calendar.py             # カレンダー同期
├── typings/
│   └── googleapiclient/
│       ├── __init__.pyi
│       └── discovery.pyi
├── .dockerignore
├── .gitignore
├── .pre-commit-config.yaml
├── .python-version
├── docker-compose.yaml
├── Dockerfile
├── main.py                            # エントリーポイント
├── pyproject.toml
├── README.md
└── uv.lock
```

---

## ⚠️ Gitルール

### ブランチ命名規則

- feature/*
- fix/*
- chore/*
- refactor/*
- hotfix/*
- docs/*

### コミットメッセージ規則

- feature: 新機能追加
- fix: 不具合修正
- chore: 環境・設定・軽微な変更
- refactor: リファクタリング
- hotfix: 緊急修正
- docs: ドキュメント変更

# ikonoijoy-schedule-sync

Webスクレイピングでイベントスケジュールを取得するプロジェクト



## 📌 概要

このプロジェクトは、複数のサイトからイベントスケジュールを取得し、構造化データとして扱うためのスクリプトです。

対象サイト：
- https://equal-love.jp/schedule
- https://not-equal-me.jp/schedule
- https://nearly-equal-joy.jp/schedule



## 🚀 機能

- スケジュール情報の自動取得
- 月ごとのデータ取得対応
- グループ別にデータ整理
- 取得データからGoogleカレンダー予定作成



## 🛠️ 使用技術

- Python 3.13
- uv
- beautifulsoup4
- google-api-python-client
- google-auth
- python-dotenv
- requests
- tzdata
- isort
- mypy
- pre-commit
- ruff
- types-requests



## 📦 セットアップ

```bash
git clone <repository-url>
cd <project-name>

uv sync
```



## ▶️ 使用方法

```bash
uv run python main.py
```



## 🧪 Lint & 型チェック

```bash
uv run ruff check .
uv run mypy .
```



## 📁 ディレクトリ構成

```
.
├── .github/
│   ├── workflows/
│   │   ├── branch_restrictions.yaml
│   │   └── ci.yaml
│   └── pull_request_template.md
├── sync/
│   ├── __init__.py
│   └── google_calendar.py
├── scraper/
│   ├── __init__.py
│   └── schedule.py
├── typings/
│   └── googleapiclient/
│       ├── __init__.pyi
│       └── discovery.pyi
├── .gitignore
├── .pre-commit-config.yaml
├── .python-version
├── main.py
├── pyproject.toml
├── uv.lock
└── README.md
```



## 📌 備考

- スクレイピング対象サイトの仕様変更に注意
- 過度なアクセスは避ける（負荷対策）
- HTML構造依存のため壊れやすい



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



## 🧑‍💻 作成者

- [tsuruoka-shun](https://github.com/tsuruoka-shun) (GitHub)

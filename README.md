# ikonoijoy-schedule-sync

Webスクレイピングでイベントスケジュールを取得するプロジェクト

---

## 📌 Overview

このプロジェクトは、複数のサイトからイベントスケジュールを取得し、構造化データとして扱うためのスクリプトです。

対象サイト：
- https://equal-love.jp/schedule/
- https://not-equal-me.jp/schedule/
- https://nearly-equal-joy.jp/schedule/

---

## 🚀 Features

- スケジュール情報の自動取得
- グループ別にデータ整理
- 月ごとのデータ取得対応
- Googleカレンダーに取得した情報から予定を作成
- 型チェック対応（mypy）
- コード整形（ruff）

---

## 🛠️ Tech Stack

- Python 3.13
- uv（パッケージ管理）
- requests
- BeautifulSoup4
- mypy
- ruff

---

## 📦 Setup

### 1. プロジェクト作成

```bash
uv init
uv python install 3.13
```

### 2. Pythonインストール

```bash
uv python install 3.13
```

### 3. 仮想環境作成

```bash
uv venv --python 3.13
```

### 4. 依存関係インストール

```bash
uv add requests beautifulsoup4
uv add --dev mypy ruff
```

## ▶️ Usage

```bash
uv run python main.py
```
または
```bash
python main.py
```
(venv有効化時)

## 🧪 Lint & Type Check
```bash
uv run ruff check .
uv run mypy .
```

## 📁 Project Structure
```bash
.
├── .github/
│   ├── workflows/
│   │   ├── branch_restrictions.yaml
│   │   └── ci.yaml
│   └── pull_request_template.md
├── calender/
│   └── add_schedules.py
├── scraper/
│   └── get_schedules.py
├── .gitignore
├── .pre-commit-config.yaml
├── .python-version
├── main.py
├── pyproject.toml
├── README.md
└── uv.lock
```

## 📌 Notes
- スクレイピング対象サイトの仕様変更に注意
- 過度なアクセスは避ける（負荷対策）
- HTML構造依存のため壊れやすい

## 🧑‍💻 Author
- [tsuruoka-shun](https://github.com/tsuruoka-shun)

## ⚠️ Git Rules

### Branch

- feature/*
- fix/*
- chore/*
- refactor/*
- hotfix/*
- docs/*

### Commit Message

- feature: 新機能追加
- fix: 不具合修正
- chore: その他の微調整・環境設定
- refactor: リファクタリング
- hotfix: 緊急修正（本番環境）
- docs: ドキュメント修正

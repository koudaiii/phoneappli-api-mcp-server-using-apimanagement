# PHONE APPLI API MCP Server using Azure API Management

[![CI](https://github.com/koudaiii/phoneappli-api-mcp-server-using-apimanagement/actions/workflows/ci.yml/badge.svg)](https://github.com/koudaiii/phoneappli-api-mcp-server-using-apimanagement/actions/workflows/ci.yml)

Azure API Management Basic v2 を使用した PHONE APPLI API の MCP サーバー実装です。

- Support バージョン
  - PHONE APPLI API バージョン [v1.20](https://developer.phoneappli.net/api/v1.20/reference.html)

## 概要

このプロジェクトは、[PHONE APPLI API](https://developer.phoneappli.net/api/v1.20/reference.html) を Azure API Management 経由で公開するためのインフラストラクチャとツールを提供します。

主な機能:
- ✅ OpenAPI Specification (v1.20.0) のバリデーション
- ✅ Azure API Management Basic v2 のプロビジョニング（Bicep + Azure Verified Modules）
- ✅ OpenAPI Spec の自動インポート
- ✅ 完全自動化されたデプロイメントスクリプト
- ✅ X-Pa-Api-Key ヘッダーの透過的な転送
- ✅ サンドボックス/本番環境の切り替え対応
- ✅ MCP (Model Context Protocol) 互換性チェックと自動英語化

## 前提条件

- **Python**: 3.11 以上
- **uv**: Python パッケージマネージャー ([インストール方法](https://docs.astral.sh/uv/))
- **Azure CLI**: Azure コマンドラインツール ([インストール方法](https://learn.microsoft.com/cli/azure/install-azure-cli))
- **yq**: YAML プロセッサー ([インストール方法](https://github.com/mikefarah/yq#install))
- **Azure サブスクリプション**: アクティブな Azure サブスクリプション

## クイックスタート

### 1. 環境のセットアップ

```bash
# リポジトリのクローン
git clone https://github.com/koudaiii/phoneappli-api-mcp-server-using-apimanagement.git
cd phoneappli-api-mcp-server-using-apimanagement

# 環境のブートストラップ（uv、Azure CLI、依存関係のインストール）
./script/bootstrap

# Azure にログイン
az login
```

### 2. OpenAPI Spec のバリデーション

```bash
./script/validate
```

出力例:
```
==> Validating OpenAPI Specification...
  File: /path/to/docs/v1.20.0.yaml

✓ File loaded successfully

┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓
┃ OpenAPI Specification Info   ┃
┗━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┛
OpenAPI Version: 3.0.3
Title: PHONE APPLI API
Version: 1.20
Paths: 45
Operations: 120

✓ Validation successful!
```

### 3. Azure へのデプロイ

```bash
# デプロイ実行（API Management 作成 + API インポート）
./script/deploy
```

環境変数でカスタマイズ可能:
```bash
# デフォルト（サンドボックス環境）
./script/deploy

# 本番環境へのデプロイ
export ENVIRONMENT="production"
./script/deploy

# その他のカスタマイズ
export LOCATION="eastus"
export DEPLOYMENT_NAME="my-custom-deployment"
export ENVIRONMENT="production"
./script/deploy
```

[MCP Server セットアップ](./docs/SETUP-MCP-SERVER.md)

### 4. リソースのクリーンアップ

```bash
./script/cleanup <resouce_group_name>
```

## プロジェクト構造

```
.
├── docs/
│   └── v1.20.0.yaml          # PHONE APPLI API OpenAPI Specification
├── infra/                     # Azure インフラストラクチャ (Bicep)
│   ├── main.bicep            # メインテンプレート
│   ├── main.bicepparam       # パラメータ定義
│   ├── resources.bicep       # 追加リソース定義
│   ├── modules/              # カスタムモジュール
│   └── README.md             # インフラドキュメント
├── script/                    # 自動化スクリプト
│   ├── bootstrap             # 環境セットアップ
│   ├── validate              # OpenAPI バリデーション
│   ├── analyzer              # API description 解析
│   ├── fix-descriptions      # Description の 1000文字制限対応
│   ├── check-mcp-compatibility # MCP 互換性チェック（タグ名、operationId、summary 抽出）
│   ├── convert-to-english    # OpenAPI 仕様書の英語化（MCP 対応）
│   ├── deploy                # デプロイ実行
│   ├── reimport              # API の再インポート
│   ├── test                  # API テスト
│   └── cleanup               # リソース削除
├── src/                       # Python 実装
│   ├── validate.py           # OpenAPI バリデーションロジック
│   ├── import_api.py         # API インポートロジック
│   └── __init__.py
├── tests/                     # テストコード
├── pyproject.toml            # Python プロジェクト設定（uv管理）
├── PLAN.md                   # 実装プラン
└── README.md                 # このファイル
```

## 使い方

### OpenAPI Spec のバリデーション

Python スクリプトを直接実行することも可能です:

```bash
uv run python src/validate.py docs/v1.20.0.yaml
```

### API Description の解析

MCPツール登録には description が1000文字以内である必要があります。現在の状態を確認:

```bash
./script/analyzer
```

出力例:
```
====================================================================================================
OpenAPI 仕様書解析結果: ./docs/v1.20.0.yaml
検出されたエンドポイント数: 45
====================================================================================================

📊 統計情報:
  📝 総エンドポイント数: 45
  ⚠️  1000文字超過: 0 個
  📏 最大記述文字数: 992
  📏 最小記述文字数: 17
  📏 平均記述文字数: 453.9
```

### Description の修正

1000文字を超える description を自動的に950文字以内に短縮（情報を保持）:

```bash
./script/fix-descriptions
```

このスクリプトは:
- 1000文字を超える description を950文字以内に短縮
- 重要な情報（パラメータ、機能、制限事項）を保持
- YAML構造を完全に保持（yqを使用）

### MCP 互換性チェック

OpenAPI 仕様書の MCP (Model Context Protocol) 互換性を確認:

```bash
./script/check-mcp-compatibility
```

出力例:
```
=====================================================================================================
MCP互換性チェック: ./docs/v1.20.0.yaml
=====================================================================================================

📊 統計情報:
  総タグ数: 11
  総エンドポイント数: 45

🔍 抽出結果:

[1] タグ名一覧
  • internal-contacts
  • profiles
  • departments
  ...

[2] operationId一覧
  • list_internal_contacts
  • create_internal_contact
  • get_internal_contact
  ...

[3] summary一覧 (MCP Tools Name)
  • List Internal Contacts
  • Create Internal Contact
  • Get Internal Contact
  ...

=====================================================================================================
✓ 抽出完了
=====================================================================================================
```

このスクリプトは:
- タグ名を抽出（MCP では ASCII 文字が必要）
- operationId を抽出（snake_case を推奨）
- summary を抽出（**MCP Tools Name として使用される**ため英語が必須）
- 新しい API バージョンリリース時の変換前後確認に使用

### OpenAPI 仕様書の英語化（MCP 対応）

新しい API バージョンがリリースされた際の英語化手順:

```bash
# 1. 現状確認
./script/check-mcp-compatibility docs/vX.XX.X.yaml

# 2. 自動変換（タグ名、operationId、summary を英語化）
./script/convert-to-english docs/vX.XX.X.yaml

# 3. 変換結果確認
./script/check-mcp-compatibility docs/vX.XX.X.yaml

# 4. バリデーション
./script/validate
```

MCP (Model Context Protocol) 要件:
- **タグ名**: 日本語 → 英語（例: `社内連絡先` → `internal-contacts`）
- **operationId**: PascalCase → snake_case（例: `UsersGet` → `list_internal_contacts`）
- **summary**: 日本語 → 英語（例: `社内連絡先一覧取得` → `List Internal Contacts`）
  - ⚠️ **重要**: summary は MCP Tools Name として使用されるため、英語が必須です

### Description の管理

各エンドポイントの description は MCP Tools として使用される際に重要な情報を提供します。

#### Description の確認

description の状態を確認:

```bash
# デフォルト（docs/v1.20.0.yaml をチェック）
./script/check-descriptions

# 別のYAMLファイルをチェック
./script/check-descriptions docs/vX.XX.X.yaml
```

このスクリプトは以下をチェック:
- ✅ 空の description を検出
- ✅ 1000文字を超える description を検出（MCP Tools の制限）
- ✅ すべての description をリスト表示

出力例:
```
=== Checking descriptions in docs/v1.20.0.yaml ===
Maximum description length for MCP Tools: 1000 characters

=== Issues ===

✅ No issues found!

=== All Descriptions ===

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Path: GET /users
Operation ID: list_internal_contacts
Summary: List Internal Contacts
Description Length: 902 chars

Description:
ツール名: List Internal Contacts
説明: 社内電話帳に登録された連絡先（ユーザ）の情報を一覧で取得します。
...

=== Summary ===
Total endpoints: 42
Empty descriptions: 0
Too long (> 1000 chars): 0
OK: 42
```

#### Description フォーマットガイドライン

description を追加する際は、`docs/sample-description-for-mcp.md` のテンプレートを参照してください:

```yaml
description: |
  ツール名: [英語のツール名]
  説明: [日本語の簡潔な説明]

  機能:
  - [機能1の説明]
  - [機能2の説明]

  パラメータ:
  必須パラメータ:
  - [パラメータ名] ([type]): [説明]

  オプションパラメータ:
  - [パラメータ名] ([type]): [説明] (デフォルト: [値])

  取得できるデータ:
  - [データ項目1]
  - [データ項目2]

  用途:
  - [ユースケース1]
  - [ユースケース2]

  制限:
  - [制限事項1]
  - APIキーごとのレート制限適用

  例:
  ```
  METHOD /path
  [リクエスト例]
  ```
```

⚠️ **重要**: description は1000文字以内に収める必要があります（MCP Tools の制限）

### API の再インポート

既存の API Management インスタンスに API を再インポート:

```bash
./script/reimport -g <resource-group> -apim <apim-name>
```

オプション:
- `-g, --resource-group`: Azure リソースグループ名（必須）
- `-apim, --apim-name`: API Management サービス名（必須）
- `-api, --api-id`: API ID（オプション、デフォルト: phoneappli-api）
- `-spec, --spec-file`: OpenAPI Spec ファイルパス（オプション、デフォルト: docs/v1.20.0.yaml）

例:
```bash
# 基本的な使い方
./script/reimport -g my-resource-group -apim my-apim-service

# カスタム設定
./script/reimport -g my-rg -apim my-apim -api custom-api-id -spec docs/custom.yaml
```

このスクリプトは:
1. OpenAPI Spec をバリデーション
2. Description の長さを解析
3. 現在のAPI設定をバックアップ
4. API を再インポート
5. 結果を表示

### API の手動インポート

既存の API Management インスタンスに API をインポート:

```bash
uv run python src/import_api.py \
  --resource-group "my-rg" \        # または -g (必須)
  --apim-name "my-apim-instance" \  # または -n (必須)
  --openapi-spec "docs/v1.20.0.yaml" \  # または -s (必須)
  --api-id "phoneappli-api" \       # オプション (デフォルト: phoneappli-api)
  --api-path "phoneappli" \         # オプション (デフォルト: phoneappli)
  --environment "sandbox"           # または -e (オプション: sandbox/production, デフォルト: sandbox)
```

環境オプション:
- `sandbox`: サンドボックス環境 (`https://api-sandbox.phoneappli.net/v1`) - デフォルト
- `production`: 本番環境 (`https://api.phoneappli.net/v1`)

本番環境へのインポート例:
```bash
uv run python src/import_api.py \
  -g "my-rg" \
  -n "my-apim-instance" \
  -s "docs/v1.20.0.yaml" \
  -e "production"
```

出力例:
```
╭──────────────────────────────────────────╮
│ Azure API Management - API Import        │
╰──────────────────────────────────────────╯

✓ Authenticated to subscription: xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx

Loading OpenAPI spec from: docs/v1.20.0.yaml
✓ Loaded API: PHONE APPLI API (v1.20)

Importing API to API Management: my-apim-instance
  Resource Group: my-rg
  API ID: phoneappli-api
  API Path: /phoneappli
  Environment: sandbox
  Backend URL: https://api-sandbox.phoneappli.net/v1

╭─ Import Result ─────────────────────────╮
│ ✓ API imported successfully!            │
│                                          │
│ API Details:                             │
│   Name: PHONE APPLI API                  │
│   Version: 1.20                          │
│   Path: /phoneappli                      │
│   API ID: phoneappli-api                 │
│   Environment: sandbox                   │
│                                          │
│ Backend URL:                             │
│   https://api-sandbox.phoneappli.net/v1 │
│                                          │
│ Gateway URL:                             │
│   https://my-apim-instance.azure-api... │
╰──────────────────────────────────────────╯
```

### Bicep テンプレートの直接デプロイ

```bash
cd infra

# パラメータファイルを編集
vim main.bicepparam

# デプロイ実行
az deployment group create \
  --name phoneappli-api-deployment \
  --resource-group phoneappli-api-mcp-rg \
  --template-file main.bicep \
  --parameters main.bicepparam
```

## 技術スタック

| カテゴリ | 技術 |
|---------|------|
| IaC | Azure Bicep with [Azure Verified Modules (AVM)](https://azure.github.io/Azure-Verified-Modules/) |
| パッケージ管理 | [uv](https://docs.astral.sh/uv/) |
| バリデーション | openapi-spec-validator |
| Azure SDK | azure-mgmt-apimanagement, azure-identity |
| CLI | click, rich |
| コード品質 | ruff, mypy |

## 環境変数

| 変数名 | 説明 | デフォルト値 |
|-------|------|------------|
| `DEPLOYMENT_NAME` | デプロイメント名（リソースグループ名としても使用） | `phoneappli-api-mcp-{timestamp}` |
| `LOCATION` | デプロイ先のリージョン | `japaneast` |
| `ENVIRONMENT` | ターゲット環境（`sandbox` または `production`） | `sandbox` |

## トラブルシューティング

### uv が見つからない

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

### yq が見つからない

macOS:
```bash
brew install yq
```

Linux:
```bash
# Debian/Ubuntu
sudo apt-get install yq

# または、バイナリを直接ダウンロード
wget https://github.com/mikefarah/yq/releases/latest/download/yq_linux_amd64 -O /usr/local/bin/yq
chmod +x /usr/local/bin/yq
```

### Azure CLI のバージョンが古い

```bash
az upgrade
```

### Azure bicep  のバージョンが古い

```bash
az bicep upgrade
```

### API Management のプロビジョニングに時間がかかる

API Management Basic v2 のプロビジョニングには通常時間がかかります。`./script/deploy` は自動的に完了を待機します。

### API インポートが失敗する

1. API Management のプロビジョニングが完了しているか確認
2. OpenAPI Spec のバリデーションが成功しているか確認: `./script/validate`
3. Azure へのログイン状態を確認: `az account show`

## 開発

### 依存関係の追加

```bash
# 本番依存関係
uv add <package-name>

# 開発依存関係
uv add --dev <package-name>
```

### コード品質チェック

```bash
# Linting
uv run ruff check .

# Type checking
uv run mypy src/

# Formatting
uv run ruff format .
```

### テストの実行

```bash
# すべてのテストを実行
./script/test

# カバレッジレポート付きでテストを実行
./script/test -c

# 詳細な出力でテストを実行
./script/test -v

# 特定のテストファイルを実行
./script/test tests/test_validate.py

# カバレッジと詳細出力の両方
./script/test -c -v

# 直接 pytest を実行する場合
uv run pytest
```

テストスクリプトのオプション:
- `-c, --coverage`: カバレッジレポートを表示
- `-v, --verbose`: 詳細な出力
- `-w, --watch`: ウォッチモード（pytest-watch が必要）
- `-h, --help`: ヘルプメッセージを表示

## ライセンス

MIT License - 詳細は [LICENSE](LICENSE) を参照してください。

## 参考資料

- [PHONE APPLI API ドキュメント v1.20](https://developer.phoneappli.net/api/v1.20/reference.html)
- [Azure API Management ドキュメント](https://learn.microsoft.com/azure/api-management/)
- [Azure Verified Modules](https://azure.github.io/Azure-Verified-Modules/)
- [uv ドキュメント](https://docs.astral.sh/uv/)

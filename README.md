# PhoneAppli API MCP Server using Azure API Management

Azure API Management Basic v2 を使用した PhoneAppli API の MCP サーバー実装です。

## 概要

このプロジェクトは、[PhoneAppli API](https://developer.phoneappli.net/) を Azure API Management 経由で公開するためのインフラストラクチャとツールを提供します。

主な機能:
- ✅ OpenAPI Specification (v1.20.0) のバリデーション
- ✅ Azure API Management Basic v2 のプロビジョニング（Bicep + Azure Verified Modules）
- ✅ OpenAPI Spec の自動インポート
- ✅ 完全自動化されたデプロイメントスクリプト
- ✅ PhoneAppli API キー（X-Pa-Api-Key）の自動設定
- ✅ サンドボックス/本番環境の切り替え対応

## 前提条件

- **Python**: 3.11 以上
- **uv**: Python パッケージマネージャー ([インストール方法](https://docs.astral.sh/uv/))
- **Azure CLI**: Azure コマンドラインツール ([インストール方法](https://learn.microsoft.com/cli/azure/install-azure-cli))
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

### 2. PhoneAppli API キーの設定

PhoneAppli API にアクセスするには API キーが必要です。[PhoneAppli Developer Portal](https://developer.phoneappli.net/) から取得してください。

```bash
# 環境変数に API キーを設定
export PHONEAPPLI_API_KEY="your-api-key"
```

**重要**: API キーは機密情報です。リポジトリにコミットしないでください。

### 3. OpenAPI Spec のバリデーション

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

### 4. Azure へのデプロイ

デプロイ前に API キーが設定されていることを確認してください。

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

### 5. リソースのクリーンアップ

```bash
./script/cleanup <resouce_group_name>
```

## プロジェクト構造

```
.
├── docs/
│   └── v1.20.0.yaml          # PhoneAppli API OpenAPI Specification
├── infra/                     # Azure インフラストラクチャ (Bicep)
│   ├── main.bicep            # メインテンプレート
│   ├── main.bicepparam       # パラメータ定義
│   ├── resources.bicep       # 追加リソース定義
│   ├── modules/              # カスタムモジュール
│   └── README.md             # インフラドキュメント
├── script/                    # 自動化スクリプト
│   ├── bootstrap             # 環境セットアップ
│   ├── validate              # OpenAPI バリデーション
│   ├── deploy                # デプロイ実行
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
| `PHONEAPPLI_API_KEY` | PhoneAppli API キー（必須） | なし |
| `DEPLOYMENT_NAME` | デプロイメント名（リソースグループ名としても使用） | `phoneappli-api-mcp-{timestamp}` |
| `LOCATION` | デプロイ先のリージョン | `japaneast` |
| `ENVIRONMENT` | ターゲット環境（`sandbox` または `production`） | `sandbox` |

## トラブルシューティング

### uv が見つからない

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
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

### API キーが設定されていない

デプロイ時に以下のエラーが表示される場合：
```
Error: PHONEAPPLI_API_KEY environment variable is not set.
```

環境変数を設定してください：
```bash
# Sandbox 環境（デフォルト）
export PHONEAPPLI_API_KEY="your-sandbox-api-key"

# Production 環境
export PHONEAPPLI_API_KEY="your-production-api-key"
```

### API インポートが失敗する

1. API Management のプロビジョニングが完了しているか確認
2. OpenAPI Spec のバリデーションが成功しているか確認: `./script/validate`
3. Azure へのログイン状態を確認: `az account show`
4. API キーが正しく設定されているか確認

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
uv run pytest
```

## ライセンス

MIT License - 詳細は [LICENSE](LICENSE) を参照してください。

## 参考資料

- [PhoneAppli API ドキュメント](https://developer.phoneappli.net/)
- [Azure API Management ドキュメント](https://learn.microsoft.com/azure/api-management/)
- [Azure Verified Modules](https://azure.github.io/Azure-Verified-Modules/)
- [uv ドキュメント](https://docs.astral.sh/uv/)

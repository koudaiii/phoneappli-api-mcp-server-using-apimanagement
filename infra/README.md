# Infrastructure as Code - Bicep

このディレクトリには、Azure API Management をデプロイするための Bicep テンプレートが含まれています。

## 前提条件

- Azure CLI がインストールされていること
- Azure サブスクリプションへのアクセス権限
- Bicep CLI（Azure CLI に含まれる）

## ファイル構成

```
infra/
├── main.bicep           # メインテンプレート（エントリーポイント）
├── main.bicepparam      # パラメータ定義
├── resources.bicep      # 追加リソース定義（将来の拡張用）
├── modules/             # カスタムモジュール
└── README.md            # このファイル
```

## 使用している Azure Verified Modules (AVM)

- **API Management Service**: `br/public:avm/res/api-management/service:0.9.0`
  - 公式ドキュメント: https://azure.github.io/Azure-Verified-Modules/

## パラメータ

### 必須パラメータ

| パラメータ名 | 説明 | デフォルト値 |
|------------|------|------------|
| `apimServiceName` | API Management サービス名（グローバルに一意） | `phoneappli-api-${uniqueString}` |
| `location` | デプロイ先のリージョン | `japaneast` |
| `publisherEmail` | 発行者のメールアドレス | `admin@example.com` |
| `publisherName` | 発行者の組織名 | `PHONE APPLI API Organization` |

### オプションパラメータ

| パラメータ名 | 説明 | デフォルト値 |
|------------|------|------------|
| `tags` | リソースに付与するタグ | `{ project: 'phoneappli-api-mcp-server', ... }` |
| `environment` | ターゲット環境（`sandbox` または `production`） | `sandbox` |

## デプロイ方法

### 1. パラメータファイルの編集

`main.bicepparam` を編集し、`publisherEmail` と `publisherName` を実際の値に変更してください。

```bicep
param publisherEmail = 'your-email@example.com'
param publisherName = 'Your Organization Name'
```

### 2. デプロイスクリプトの実行

プロジェクトルートから以下のコマンドを実行します。

```bash
# PHONE APPLI API キーの設定（必須）
export PHONEAPPLI_API_KEY="your-api-key"

# 環境変数の設定（オプション）
export ENVIRONMENT="sandbox"  # または "production"
export LOCATION="japaneast"

# デプロイ実行
./script/deploy
```

### 3. 手動デプロイ（Azure CLI を直接使用）

```bash
# リソースグループの作成
az group create \
  --name phoneappli-api-mcp-rg \
  --location japaneast

# Bicep テンプレートのデプロイ
az deployment group create \
  --name phoneappli-api-mcp-deployment \
  --resource-group phoneappli-api-mcp-rg \
  --template-file main.bicep \
  --parameters main.bicepparam \
  --parameters environment="sandbox"
```

## デプロイ後の確認

デプロイが完了すると、以下の出力が表示されます。

```
apimServiceName       : phoneappli-api-xxxxx
apimResourceId        : /subscriptions/.../resourceGroups/.../providers/Microsoft.ApiManagement/service/...
apimGatewayUrl        : https://phoneappli-api-xxxxx.azure-api.net
systemAssignedPrincipalId : xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx
```

### Azure Portal での確認

```bash
# ブラウザで Azure Portal を開く
az apim show \
  --name <apimServiceName> \
  --resource-group phoneappli-api-mcp-rg \
  --query id -o tsv | xargs -I {} open "https://portal.azure.com/#resource{}"
```

## リソースの削除

すべてのリソースを削除するには、以下のコマンドを実行します。

```bash
./script/cleanup <resouce_group_name>
```

または、手動で削除する場合：

```bash
az group delete \
  --name phoneappli-api-mcp-rg \
  --yes \
  --no-wait
```

## トラブルシューティング

### デプロイエラー: "The service name is already in use"

API Management サービス名はグローバルに一意である必要があります。`main.bicepparam` で異なる名前を指定してください。

### デプロイに時間がかかる

API Management のプロビジョニングには 30〜45 分程度かかる場合があります。

### Bicep モジュールが見つからない

Bicep CLI のバージョンが古い可能性があります。以下のコマンドで最新版に更新してください。

```bash
az bicep upgrade
```

## 参考資料

- [Azure API Management ドキュメント](https://learn.microsoft.com/ja-jp/azure/api-management/)
- [Azure Verified Modules](https://azure.github.io/Azure-Verified-Modules/)
- [Bicep ドキュメント](https://learn.microsoft.com/ja-jp/azure/azure-resource-manager/bicep/)

#!/usr/bin/env python3
"""
OpenAPI 仕様書のエンドポイント記述文字数解析ツール

【概要】
このプログラムは、OpenAPI 仕様書（YAML形式）を解析し、各エンドポイントの
description フィールドの文字数をカウント・表示するツールです。

【主な機能】
1. 全エンドポイントの description 文字数を調査
2. 1000文字を超えるエンドポイントを特定・警告表示
3. 文字数順（降順）でソート表示
4. 統計情報の表示（合計数、最大・最小文字数など）
5. 1000文字超過エンドポイントの詳細情報表示

【想定される使用場面】
- API Management でのMCPサーバー作成時の事前チェック
- OpenAPI仕様書の品質管理
- ドキュメント文字数制限の確認
- API仕様書のメンテナンス作業

【想定される結果例】
```
==========================================
OpenAPI Spec: docs/v1.20.0.yaml
Total endpoints: 25
==========================================

Summary:
  Total endpoints: 25
  Endpoints exceeding 1000 chars: 3
  Max description length: 1250
  Min description length: 45

Method   Path                              Length   Status      Summary
------------------------------------------------------------------------
POST     /api/v1/users                       1250   ⚠️ EXCEEDS   Create new user account...
GET      /api/v1/orders/{id}                 1150   ⚠️ EXCEEDS   Retrieve order details...
PUT      /api/v1/products/{id}               1050   ⚠️ EXCEEDS   Update product information...
GET      /api/v1/health                        45   ✓ OK        Health check endpoint
```

【使用方法】
```bash
# デフォルトファイル（docs/v1.20.0.yaml）を解析
python src/analyze_descriptions.py

# 特定のファイルを解析
python src/analyze_descriptions.py path/to/your/openapi.yaml
```
"""

import yaml
import sys
from pathlib import Path


def count_description_lengths(spec_file: str):
    """
    OpenAPI仕様書を読み込み、各エンドポイントのdescription文字数をカウント

    Args:
        spec_file (str): OpenAPI YAML ファイルのパス
    
    Returns:
        None: 結果は標準出力に表示
    
    処理の流れ:
    1. YAML ファイルの読み込み
    2. 全エンドポイントの走査と情報収集
    3. 文字数による降順ソート
    4. 統計情報と一覧の表示
    5. 1000文字超過エンドポイントの詳細表示
    """
    # YAML ファイルを UTF-8 エンコーディングで読み込み
    # safe_load() を使用してセキュアに解析
    try:
        with open(spec_file, 'r', encoding='utf-8') as f:
            spec = yaml.safe_load(f)
    except FileNotFoundError:
        print(f"エラー: ファイル '{spec_file}' が見つかりません")
        return
    except yaml.YAMLError as e:
        print(f"エラー: YAML パース エラー - {e}")
        return
    except Exception as e:
        print(f"エラー: ファイル読み込み失敗 - {e}")
        return

    # エンドポイント情報を格納するリスト
    endpoints = []

    # OpenAPI仕様の基本構造チェック
    if 'paths' not in spec:
        print("エラー: OpenAPI 仕様に 'paths' セクションが見つかりません")
        return

    # 全パスとHTTPメソッドを走査
    for path, path_item in spec['paths'].items():
        # サポートする HTTP メソッド一覧
        # OpenAPI 3.0 で定義されている標準メソッド
        supported_methods = ['get', 'post', 'put', 'patch', 'delete', 'options', 'head', 'trace']
        
        for method in supported_methods:
            if method in path_item:
                operation = path_item[method]
                
                # 各フィールドを安全に取得（存在しない場合は空文字）
                description = operation.get('description', '')
                summary = operation.get('summary', '')
                operation_id = operation.get('operationId', '')

                # 文字数をカウント（Unicode文字も正確にカウント）
                desc_length = len(description)

                # エンドポイント情報を辞書として保存
                endpoints.append({
                    'method': method.upper(),          # HTTPメソッドを大文字で統一
                    'path': path,                      # APIパス
                    'operation_id': operation_id,      # 操作ID
                    'summary': summary,                # 要約
                    'description_length': desc_length, # 記述文字数
                    'description': description,        # 記述内容（全文）
                    'exceeds_1000': desc_length > 1000 # 1000文字超過フラグ
                })

    # 記述文字数の降順でソート
    # lambda関数でdescription_lengthをキーとして使用
    endpoints.sort(key=lambda x: x['description_length'], reverse=True)

    # === 結果表示部分 ===
    
    # メインヘッダーの表示
    print("=" * 100)
    print(f"OpenAPI 仕様書解析結果: {spec_file}")
    print(f"検出されたエンドポイント数: {len(endpoints)}")
    print("=" * 100)
    print()

    # 統計情報の計算と表示
    total_endpoints = len(endpoints)
    exceeding_endpoints = [ep for ep in endpoints if ep['exceeds_1000']]  # 1000文字超過エンドポイントをフィルタ
    exceeding_count = len(exceeding_endpoints)

    print(f"📊 統計情報:")
    print(f"  📝 総エンドポイント数: {total_endpoints}")
    print(f"  ⚠️  1000文字超過: {exceeding_count} 個")
    if exceeding_count > 0:
        print(f"     超過率: {exceeding_count/total_endpoints*100:.1f}%")
    
    # 最大・最小文字数の表示（エンドポイントが存在する場合のみ）
    if endpoints:
        max_length = endpoints[0]['description_length']  # ソート済みなので最初が最大
        min_length = endpoints[-1]['description_length'] # 最後が最小
        print(f"  📏 最大記述文字数: {max_length}")
        print(f"  📏 最小記述文字数: {min_length}")
        
        # 平均文字数も計算
        avg_length = sum(ep['description_length'] for ep in endpoints) / total_endpoints
        print(f"  📏 平均記述文字数: {avg_length:.1f}")
    print()

    # エンドポイント一覧テーブルの表示
    print("-" * 100)
    print(f"{'Method':<8} {'Path':<40} {'Length':>8} {'Status':<12} {'Summary':<30}")
    print("-" * 100)

    for ep in endpoints:
        # 1000文字超過の場合は警告アイコン、そうでなければOKアイコン
        status = "⚠️ EXCEEDS" if ep['exceeds_1000'] else "✅ OK"
        
        # summaryが長い場合は省略表示（30文字制限）
        summary_short = (ep['summary'][:27] + '...') if len(ep['summary']) > 30 else ep['summary']
        
        # テーブル行を整形して表示
        print(f"{ep['method']:<8} {ep['path']:<40} {ep['description_length']:>8} {status:<12} {summary_short:<30}")

    print("-" * 100)
    print()

    # 1000文字を超過するエンドポイントの詳細表示
    if exceeding_endpoints:
        print("=" * 100)
        print("🚨 1000文字を超過するエンドポイントの詳細情報")
        print("=" * 100)
        print()

        for i, ep in enumerate(exceeding_endpoints, 1):
            print(f"📍 {i}. {ep['method']} {ep['path']}")
            print(f"   🔖 操作ID: {ep['operation_id'] or '未設定'}")
            print(f"   📝 要約: {ep['summary'] or '未設定'}")
            print(f"   📏 記述文字数: {ep['description_length']} 文字")
            print(f"   ⚠️  超過文字数: {ep['description_length'] - 1000} 文字")
            print()
            
            # 記述内容の先頭200文字をプレビュー表示
            print("   📄 記述内容プレビュー（先頭200文字）:")
            preview = ep['description'][:200]
            # 改行を含む場合は適切にインデント
            preview_lines = preview.split('\n')
            for line in preview_lines:
                print(f"   {line}")
            if len(ep['description']) > 200:
                print("   ...")
            print()
            print("-" * 100)
            print()


def main():
    """
    メイン関数: コマンドライン引数の処理とプログラム実行
    
    コマンドライン使用法:
    - python analyze_descriptions.py                    # デフォルトファイル使用
    - python analyze_descriptions.py custom/path.yaml  # カスタムファイル指定
    """
    # デフォルトの仕様書ファイルパス
    # プロジェクトルートからの相対パス
    default_spec_file = 'docs/v1.20.0.yaml'
    
    # コマンドライン引数の処理
    if len(sys.argv) > 1:
        # 引数が指定された場合はそのファイルを使用
        spec_file = sys.argv[1]
        print(f"🔍 指定されたファイル: {spec_file}")
    else:
        # 引数が指定されていない場合はデフォルトファイルを使用
        spec_file = default_spec_file
        print(f"🔍 デフォルトファイル: {spec_file}")

    # ファイル存在チェック
    spec_path = Path(spec_file)
    if not spec_path.exists():
        print(f"❌ エラー: ファイル '{spec_file}' が見つかりません")
        print(f"   現在のディレクトリ: {Path.cwd()}")
        print(f"   探索パス: {spec_path.absolute()}")
        sys.exit(1)
    
    # ファイル拡張子のチェック（YAML/YMLファイルのみ対応）
    if spec_path.suffix.lower() not in ['.yaml', '.yml']:
        print(f"⚠️  警告: '{spec_file}' はYAMLファイルではないようです")
        print("   続行しますが、パースエラーが発生する可能性があります")

    print(f"✅ ファイル確認完了")
    print()

    # メイン処理の実行
    count_description_lengths(spec_file)


if __name__ == '__main__':
    main()

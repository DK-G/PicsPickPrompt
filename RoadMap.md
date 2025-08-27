# RoadMap

このプロジェクトの開発計画とスプリントのロードマップです。

## ゴール
- 画像→プロンプトの自動化を、photo/anime × single/group × upper/fullbody で安定運用。
- プロンプトは常に 55–65語、人名/数値/メタなし、矛盾なし。
- ルーター（style/profile）で自動切替。CLIで上書き可能。
- ログとバリデータで"壊れていない"ことを自動確認。

## スプリント計画
### Sprint 0: 固める
- 既存動作を既定（photo×single_upper）として固定化、バリデータ導入（OK/FAIL）。

### Sprint 1: ルーター実装
- Style Router（photo/anime）、Subject Router（single/group × upper/full）。

### Sprint 2: プロファイル別ルール
- 背景一本化ON/OFF、下半身衣類の削除ON/OFF、フレーミング語の上限など。

### Sprint 3: SAFE_FILL 分離
- photo/anime × 4プロファイルのSAFE_FILLプール整備、競合/重複ガード。

### Sprint 4: 矛盾・正規化の強化
- animeでの実写語抑制、構図/焦点/視線の矛盾消し、再混入ブロック。

### Sprint 5: テストとCI
- 検証セットで一括評価、CIにバリデータ（回帰防止）。

### Sprint 6: ドキュメント & サンプル
- README/使い方、ログの読み方、失敗時のFAQ。

### （任意）Sprint 7: UI/統合
- ComfyUIノード化や簡易バッチGUI。

## 成果物
- コード（style/profileルーター、プロファイル別SAFE_FILL、正規化＆矛盾ルール）。
- バリデータ（prompt_validator.py：長さ・矛盾・背景語・スタイル漏れをチェック）。
- 検証用ミニデータセット（6枚：photo/anime × single/group × upper/full）。
- ドキュメント（README、CLIの使い方、ログ仕様、DoDチェックリスト）。

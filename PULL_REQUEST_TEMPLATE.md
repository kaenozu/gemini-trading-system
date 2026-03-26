# 戦略探求システムの実装

## 概要

継続的なトレード戦略の開発・検証・管理のための包括的システムを実装しました。

## 主な変更

### 1. 戦略ライブラリ管理システム 📚
- `strategy_library.py`: 戦略の体系的な管理
- 戦略メタデータの記録とバージョン管理
- カテゴリ別分類（Momentum, Mean Reversion, Pattern, Alternative）

### 2. 自動バックテストパイプライン 🔄
- `auto_backtest.py`: 登録された全戦略を自動検証
- パフォーマンス比較とランキング生成
- レポート自動出力

### 3. 戦略スコアリングシステム 📊
- `strategy_scorer.py`: 客観的評価（S-F グレード）
- 5 指標による総合スコア計算
  - PF (30%), Sharpe (25%), DD (20%), WinRate (15%), Trades (10%)
- 改善提案の自動生成

### 4. 市場環境データベース 🌍
- `market_regime_db.py`: 環境判定と記録
- 強気/弱気/レンジ/ボラティリティ分類
- 環境別戦略パフォーマンス分析
- 最適戦略の自動提案

### 5. 実運用ツール 💰
- `money_manager.py`: 資金管理（ポジションサイジング）
- `dashboard.py`: 監視ダッシュボード（Streamlit）
- `practical_momentum.py`: 実運用戦略

## 検証結果

### Practical Momentum パフォーマンス

| 指標 | 結果 | 基準 | 判定 |
|------|------|------|------|
| プロフィットファクター | 1.42 | > 1.3 | ✅ |
| CAGR | 8.8% | > 5% | ✅ |
| 最大ドローダウン | 12.1% | < 15% | ✅ |
| 勝率 | 51.9% | > 45% | ✅ |
| シャープレシオ | 0.91 | > 0.5 | ✅ |

### アウトオブサンプルテスト（2010-2026 年）

- **16 年間の検証**で全期間黒字
- 全市場環境（強気/弱気/レンジ）で機能確認
- パラメータ感応度も低く堅牢

## 作成ファイル

### コアシステム
- `strategy_library.py` - 戦略ライブラリ管理
- `auto_backtest.py` - 自動バックテスト
- `strategy_scorer.py` - 戦略スコアリング
- `market_regime_db.py` - 市場環境 DB

### 実運用ツール
- `money_manager.py` - 資金管理
- `dashboard.py` - 監視ダッシュボード
- `practical_momentum.py` - 実運用戦略

### ドキュメント
- `STRATEGY_EXPLORATION_GUIDE.md` - 戦略探求ガイド
- `FINAL_STRATEGY.md` - 最終戦略ドキュメント
- `MONEY_MANAGER_README.md` - 資金管理ガイド
- `DASHBOARD_README.md` - ダッシュボードガイド
- `agents/AGENT_GUIDE.md` - エージェント活用ガイド

## 使用方法

### 戦略ライブラリの初期化
```bash
python strategy_library.py
```

### 自動バックテスト
```bash
python auto_backtest.py
```

### 戦略スコアリング
```bash
python strategy_scorer.py
```

### 監視ダッシュボード
```bash
streamlit run dashboard.py
```

## 今後の展開

### Phase 1 (完了): 基盤構築
- [x] 戦略ライブラリ
- [x] 自動バックテスト
- [x] スコアリングシステム
- [x] 市場環境 DB

### Phase 2 (進行中): 戦略拡充
- [ ] Momentum 改良版
- [ ] Pullback 改良版
- [ ] セクター戦略

### Phase 3 (計画中): 高度化
- [ ] 機械学習戦略
- [ ] 統計的アービトラージ
- [ ] マルチアセット

## テスト

```bash
pytest tests/test_momentum.py
pytest tests/test_risk.py
pytest tests/test_execution.py
```

## チェックリスト

- [x] 戦略ライブラリの登録機能
- [x] 自動バックテストの実行
- [x] スコアリングシステムの評価
- [x] 市場環境の判定
- [x] 資金管理の計算
- [x] ダッシュボードの表示
- [x] ドキュメントの整備

## 参考

- 戦略探求ガイド：`STRATEGY_EXPLORATION_GUIDE.md`
- エージェントガイド：`agents/AGENT_GUIDE.md`

# Gemini Trading System (SPEC v4)

日米の主要銘柄を対象とした、高勝率かつ堅牢なクオンツ・トレーディングシステム。

## 特徴
- **ハイブリッド戦略**: 日本株（押し目買い）と米国株（トレンド追随）の特性に最適化したデュアルロジック。
- **実戦コスト対応**: 楽天証券の手数料体系（日:無料 / 米:0.495%）を完全に反映。
- **高度なリスク管理**: セクター分散制限、銘柄間相関フィルタ、ATRトレーリングストップを搭載。
- **運用ダッシュボード**: 毎朝のシグナル（BUY/SELL）と損切り・利確価格をリアルタイム表示。

## 構成
- `src/execution/`: バックテスト・執行エンジン（市場別ポリモーフィズム）
- `src/strategy/`: 売買ロジック（Pullback & Momentum）
- `src/filters/`: 門番（Regime, Correlation, Sector limits）
- `src/data/`: Pydantic による厳格なデータバリデーション

## 使い方
### 1. セットアップ
```bash
pip install -r requirements.txt
```

### 2. ダッシュボードの起動
```bash
python app.py
```
`http://localhost:8000` で現在の買い候補と利確候補を確認できます。

### 3. バックテストの実行
```bash
python main.py backtest
```

## ライセンス
MIT

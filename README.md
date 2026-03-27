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

### 自動戦略選択の調整（環境変数）
`main.py scan` / `app.py` の `Scanner` は、以下の環境変数で挙動を変更できます。

- `SCANNER_AUTO_SELECT` (default: `true`)
- `SCANNER_REFRESH_DATA` (default: `false`)  ※ `false` でローカル parquet 優先になり高速
- `SCANNER_START_DATE` (default: `2023-01-01`)  ※ `refresh_data=true` 時の取得開始日
- `SCANNER_LOOKBACK_DAYS` (default: `252`)
- `SCANNER_SELECTOR_DD_PENALTY` (default: `1.0`)
- `SCANNER_SELECTOR_WF_WINDOWS` (default: `5`)
- `SCANNER_SELECTOR_WF_VALID_DAYS` (default: `63`)
- `SCANNER_MIN_SELECT_SCORE` (default: `0.005`)
- `SCANNER_SWITCH_HYSTERESIS` (default: `0.01`)
- `SCANNER_US_STRATEGIES` / `SCANNER_JP_STRATEGIES`（カンマ区切り）
- `SCANNER_SELECTION_LOG_PATH`（default: `paper_trading_results/strategy_selection_log.csv`）

PowerShell 例:
```powershell
$env:SCANNER_MIN_SELECT_SCORE = "0.003"
$env:SCANNER_SELECTOR_DD_PENALTY = "0.7"
python main.py scan
```

実運用向けの最適化プリセット（高速 + 候補絞り込み）:
```powershell
$env:SCANNER_REFRESH_DATA = "false"
$env:SCANNER_US_STRATEGIES = "MomentumV2Strategy,MeanReversionV2Strategy"
$env:SCANNER_JP_STRATEGIES = "MeanReversionV2Strategy,PullbackStrategy"
$env:SCANNER_SELECTOR_DD_PENALTY = "1.0"
$env:SCANNER_SELECTOR_WF_WINDOWS = "5"
$env:SCANNER_SELECTOR_WF_VALID_DAYS = "63"
$env:SCANNER_MIN_SELECT_SCORE = "0.005"
python main.py scan
```

### 3. バックテストの実行
```bash
python main.py backtest
```

## ライセンス
MIT

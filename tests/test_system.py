import pytest
import pandas as pd
import numpy as np
from src.risk.manager import RiskManager
from src.features.engine import FeatureEngine

def test_risk_manager_position_sizing():
    manager = RiskManager(risk_per_trade_pct=0.01)
    # 100k capital, entry 100, stop 90 (risk 10 per share)
    # 1% risk = 1000. Shares = 1000 / 10 = 100
    shares = manager.calculate_position_size(100000, 100, 90)
    assert shares == 100

def test_feature_engine_rsi():
    fe = FeatureEngine()
    df = pd.DataFrame({'Close': [100, 101, 102, 101, 100, 99, 98, 99, 100, 101, 102, 103, 104, 105, 106]}, 
                      index=pd.date_range('2026-01-01', periods=15))
    df['High'] = df['Close'] + 1
    df['Low'] = df['Close'] - 1
    df['Volume'] = 1000
    
    df_with_ind = fe.add_indicators(df)
    assert 'RSI_14' in df_with_ind.columns
    assert not df_with_ind['RSI_14'].isna().iloc[-1]

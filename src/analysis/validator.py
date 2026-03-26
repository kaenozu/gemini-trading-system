import pandas as pd

class WalkForwardValidator:
    """
    SPEC v4 compliant Walk-Forward Validator.
    Divides data into In-sample (train) and Out-of-sample (test) to prevent overfitting.
    """
    def __init__(self, train_months: int = 12, test_months: int = 3):
        # 1 month approx 21 trading days
        self.train_days = train_months * 21
        self.test_days = test_months * 21

    def validate(self, engine_class, ticker_data, bench_data):
        """
        Runs walk-forward validation and returns list of Profit Factors per window.
        """
        results = []
        total_len = len(ticker_data)
        
        for i in range(self.train_days, total_len - self.test_days, self.test_days):
            train_set = ticker_data.iloc[i-self.train_days : i]
            test_set = ticker_data.iloc[i : i + self.test_days]
            
            engine = engine_class()
            log = engine.run(train_set, bench_data)
            
            if not log.empty and 'PnL' in log.columns:
                wins = log[log['PnL'] > 0]['PnL'].sum()
                losses = abs(log[log['PnL'] < 0]['PnL'].sum())
                pf = wins / losses if losses != 0 else wins
                results.append(pf)
            else:
                results.append(0.0)
                
        return results

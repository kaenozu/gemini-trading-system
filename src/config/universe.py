"""
Centralized ticker universe configuration.
Defines the list of stocks to scan and trade.
"""

# US Stocks - Major tech and growth companies
TICKERS_US = [
    "AAPL",  # Apple
    "MSFT",  # Microsoft
    "GOOGL",  # Alphabet
    "AMZN",  # Amazon
    "NVDA",  # NVIDIA
    "META",  # Meta Platforms
    "TSLA",  # Tesla
    "AVGO",  # Broadcom
    "ADBE",  # Adobe
    "AMD",  # AMD
]

# Japanese Stocks - Major companies across sectors
TICKERS_JP = [
    "7203.T",  # Toyota
    "6758.T",  # Sony
    "9984.T",  # SoftBank
    "6861.T",  # Keyence
    "8035.T",  # Tokyo Electron
    "6981.T",  # Murata
    "6501.T",  # Hitachi
    "6098.T",  # Recruit
    "9432.T",  # NTT
    "8306.T",  # Mitsubishi UFJ
    "7974.T",  # Nintendo
    "4063.T",  # Shin-Etsu
    "6702.T",  # Fujitsu
    "6367.T",  # Daikin
    "6723.T",  # Renesas
    "9983.T",  # Fast Retailing
    "7741.T",  # Hoya
    "4568.T",  # Daiichi Sankyo
    "6594.T",  # Nidec
    "6146.T",  # Disco
]

# Combined universe
TICKERS_ALL = TICKERS_US + TICKERS_JP

# Sector mapping for portfolio diversification
SECTORS = {
    # US Tech
    "AAPL": "Tech",
    "MSFT": "Tech",
    "GOOGL": "Tech",
    "NVDA": "Tech",
    "META": "Tech",
    "AVGO": "Tech",
    "ADBE": "Tech",
    "AMD": "Tech",
    # US Consumer
    "AMZN": "Consumer",
    "TSLA": "Consumer",
    # JP Auto
    "7203.T": "Auto",
    # JP Tech
    "6758.T": "Tech",
    "6861.T": "Tech",
    "8035.T": "Tech",
    "6981.T": "Tech",
    "6702.T": "Tech",
    "6723.T": "Tech",
    "7741.T": "Tech",
    # JP Finance
    "9984.T": "Finance",
    "6098.T": "Finance",
    "8306.T": "Finance",
    # JP Industrial
    "6501.T": "Industrial",
    "6367.T": "Industrial",
    "6594.T": "Industrial",
    "6146.T": "Industrial",
    # JP Comms
    "9432.T": "Comms",
    # JP Consumer
    "7974.T": "Consumer",
    "9983.T": "Consumer",
    # JP Materials
    "4063.T": "Materials",
    # JP Healthcare
    "4568.T": "Healthcare",
}

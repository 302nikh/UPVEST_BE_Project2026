from market_data_fetcher import get_market_data
import json

symbol = "NSE_EQ|INE155A01022"
stock_name = "ASIANPAINT"

print(f"Testing {stock_name} ({symbol})...")
price, indicators = get_market_data(symbol, interval="5minute", days=1, stock_name=stock_name)

print(f"Price: {price}")
print(f"Indicators: {indicators}")

import yfinance as yf


def get_ext_price(symbol: str, include_extended_hours: bool = True) -> float:
	ticker = yf.Ticker(symbol)
	info = ticker.info or {}

	if include_extended_hours:
		# Prefer explicit post-market and pre-market quotes when available.
		post_market_price = info.get("postMarketPrice")
		if post_market_price is not None:
			return round(float(post_market_price), 2)

		pre_market_price = info.get("preMarketPrice")
		if pre_market_price is not None:
			return round(float(pre_market_price), 2)

		# Fallback for extended hours: latest intraday trade including pre/post data.
		intraday = ticker.history(period="1d", interval="1m", prepost=True)
		if not intraday.empty:
			close_series = intraday["Close"].dropna()
			if not close_series.empty:
				return round(float(close_series.iloc[-1]), 2)

	# Try the most up-to-date value first.
	fast_info = ticker.fast_info or {}
	last_price = fast_info.get("lastPrice")
	if last_price is not None:
		return round(float(last_price), 2)

	# Fallback: use latest close from recent history.
	history = ticker.history(period="5d")
	if history.empty:
		raise RuntimeError(f"Unable to fetch {symbol} price from yfinance")
	return round(float(history["Close"].iloc[-1]), 2)

def get_lastPrice(symbol: str) -> float:
	ticker = yf.Ticker(symbol)

	# Try the most up-to-date value first.
	fast_info = ticker.fast_info
	last_price = fast_info.get("lastPrice")
	if last_price is not None:
		return round(float(last_price), 2)

	# Fallback: use latest close from recent history.
	history = ticker.history(period="5d")
	if history.empty:
		raise RuntimeError(f"Unable to fetch {symbol} price from yfinance")

	return round(float(history["Close"].iloc[-1]), 2)

if __name__ == "__main__":
	print (get_ext_price("TSLA"))
	#price = get_current_price('TSLA')
	#print(f"Current TSLA price: ${price:.2f}")
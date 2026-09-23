#!/usr/bin/env python3
"""market_snapshot.py — yfinance'ten günün gerçek piyasa verisi (JSON, stdout). LLM sadece bu rakamları kullanır.
Veri 15 dk gecikmeli olabilir; "anlık" denmez.
"""
import datetime, json, os, sys

import yfinance as yf

TR = os.environ.get("CONTENT_LANG", "en") == "tr"
NAMES = {"BTC-USD": "Bitcoin", "ETH-USD": "Ethereum", "SOL-USD": "Solana", "XU100.IS": "BIST 100",
         "USDTRY=X": "Dolar/TL" if TR else "USD/TRY", "EURTRY=X": "Euro/TL" if TR else "EUR/TRY",
         "GC=F": "Altın (ons)" if TR else "Gold", "SI=F": "Gümüş" if TR else "Silver",
         "^GSPC": "S&P 500", "^IXIC": "Nasdaq", "^DJI": "Dow Jones", "^VIX": "VIX",
         "CL=F": "Petrol (WTI)" if TR else "Oil (WTI)", "DX-Y.NYB": "Dolar Endeksi" if TR else "Dollar Index",
         "NVDA": "Nvidia", "TSLA": "Tesla", "AAPL": "Apple", "MSFT": "Microsoft", "AMZN": "Amazon",
         "META": "Meta", "GOOGL": "Google"}
TICKERS = os.environ.get("MARKET_TICKERS", "^GSPC,^IXIC,^DJI,GC=F,CL=F,DX-Y.NYB,NVDA,AAPL,MSFT,TSLA,AMZN,META").split(",")


def snap(sym):
    h = yf.Ticker(sym).history(period="2mo", interval="1d")["Close"].dropna()
    if len(h) < 6:
        return None
    last, prev, wk = float(h.iloc[-1]), float(h.iloc[-2]), float(h.iloc[-6])
    return {"name": NAMES.get(sym, sym), "price": round(last, 2),
            "change_pct": round((last / prev - 1) * 100, 2),
            "change_5d_pct": round((last / wk - 1) * 100, 2),
            "as_of": str(h.index[-1].date()),
            "series": [round(float(x), 4) for x in h.iloc[-30:]]}


def main():
    out = {"date": datetime.date.today().isoformat(), "note": "gecikmeli kapanış verisi", "tickers": {}}
    for s in (t.strip() for t in TICKERS if t.strip()):
        try:
            d = snap(s)
            if d:
                out["tickers"][s] = d
        except Exception as e:
            print(f"skip {s}: {e}", file=sys.stderr)
    if not out["tickers"]:
        sys.exit("hiç piyasa verisi alınamadı")
    print(json.dumps(out, ensure_ascii=False))


if __name__ == "__main__":
    main()

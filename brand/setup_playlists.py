#!/usr/bin/env python3
"""setup_playlists.py — kanal oynatma listeleri + ana sayfa rafları (bir kez; tekrar çalıştırmak güvenli).
Liste kimlikleri state/playlists.json'a yazılır; daily_viral.py her videoyu konusuna göre listeye ekler.
"""
import json, pathlib, sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from common import STATE, yt_creds  # noqa: E402

PLAYLISTS = [
    {"key": "bigtech", "title": "Big Tech Moves: Nvidia, Apple, Tesla & more",
     "desc": "Why Nvidia, Apple, Microsoft, Tesla, Amazon, Meta and Google moved, one real move at a time. Not financial advice.",
     "tickers": ["NVDA", "AAPL", "MSFT", "TSLA", "AMZN", "META", "GOOGL"]},
    {"key": "indexes", "title": "S&P 500, Nasdaq & Dow Explained",
     "desc": "What moved the whole market today, and what it means for your portfolio. Not financial advice.",
     "tickers": ["^GSPC", "^IXIC", "^DJI", "^VIX"]},
    {"key": "macro", "title": "Gold, Oil, the Dollar & the Fed",
     "desc": "Gold, oil, the dollar and interest rates: how they moved and why stocks care. Not financial advice.",
     "tickers": ["GC=F", "SI=F", "CL=F", "DX-Y.NYB"]},
    {"key": "recap", "title": "Daily Market Recap",
     "desc": "The whole board in under 40 seconds: the biggest movers of the day. Not financial advice.",
     "tickers": []},
]


def main():
    from googleapiclient.discovery import build
    yt = build("youtube", "v3", credentials=yt_creds(), cache_discovery=False)
    existing = {p["snippet"]["title"]: p["id"]
                for p in yt.playlists().list(part="snippet", mine=True, maxResults=50).execute().get("items", [])}
    out = {"by_key": {}, "by_ticker": {}}
    for pl in PLAYLISTS:
        pid = existing.get(pl["title"])
        if not pid:
            pid = yt.playlists().insert(part="snippet,status", body={
                "snippet": {"title": pl["title"], "description": pl["desc"], "defaultLanguage": "en"},
                "status": {"privacyStatus": "public"}}).execute()["id"]
            print(f"✓ liste oluşturuldu: {pl['title']}")
        else:
            print(f"• liste zaten var: {pl['title']}")
        out["by_key"][pl["key"]] = pid
        for t in pl["tickers"]:
            out["by_ticker"][t] = pid
    (STATE / "playlists.json").write_text(json.dumps(out, indent=1), encoding="utf-8")

    # ana sayfa rafları (Shorts rafını YouTube kendisi ekler)
    try:
        have = {s["contentDetails"]["playlists"][0] for s in
                yt.channelSections().list(part="contentDetails", mine=True).execute().get("items", [])
                if s.get("contentDetails", {}).get("playlists")}
        for pos, key in enumerate(["bigtech", "indexes", "macro", "recap"]):
            pid = out["by_key"][key]
            if pid in have:
                continue
            yt.channelSections().insert(part="snippet,contentDetails", body={
                "snippet": {"type": "singlePlaylist", "position": pos},
                "contentDetails": {"playlists": [pid]}}).execute()
            print(f"✓ ana sayfa rafı: {key}")
    except Exception as e:
        print(f"• ana sayfa rafları atlandı ({str(e)[:160]}) — Studio → Özelleştirme → Düzen'den eklenebilir")
    print("state/playlists.json yazıldı")


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""apply_branding.py — kanal ayarlarını YouTube API ile uygular (auth_youtube.py'den sonra, bir kez).

    python brand/apply_branding.py              # önce ne yapacağını gösterir, onay ister
    python brand/apply_branding.py --yes        # sormadan uygula
    python brand/apply_branding.py --country DE # yaşadığın ülke (ISO kodu), opsiyonel

API ile YAPILAMAYANLAR (Studio'dan elle): kanal adı ve handle (kanal açılırken), profil resmi,
yorum filtreleri / engellenen kelimeler, iletişim e-postası.
"""
import pathlib, sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))
from common import yt_creds  # noqa: E402

HERE = pathlib.Path(__file__).resolve().parent
EXPECTED = "Why Stocks Moved"

DESCRIPTION = """Every day, one real market move explained in under 40 seconds.

Why did Nvidia jump? Why is oil falling? What does the Fed decision mean for your portfolio? Each Short takes one move from today's market data, shows you the chart, and explains the cause in plain English: stocks, big tech, earnings, rates, inflation, gold, oil and the dollar.

Real numbers only. No hype, no price predictions, no "buy now".

New Shorts every day at 12:30 PM and 7 PM ET.

Not financial advice. Market data may be delayed. Everything here is for education and information only. Do your own research before making any investment decision."""

KEYWORDS = ["why stocks moved", "stock market today", "stock market news", "stocks explained",
            "why is the stock market down", "why is the stock market up", "nvidia stock", "tesla stock",
            "apple stock", "big tech stocks", "fed rate decision", "inflation explained", "gold price",
            "oil price", "s&p 500", "nasdaq", "investing for beginners", "personal finance", "market recap",
            "stock market shorts"]


def main():
    from googleapiclient.discovery import build
    from googleapiclient.http import MediaFileUpload

    a = sys.argv[1:]
    country = a[a.index("--country") + 1].upper() if "--country" in a else None
    yt = build("youtube", "v3", credentials=yt_creds(), cache_discovery=False)
    ch = yt.channels().list(part="snippet,brandingSettings,status", mine=True).execute()["items"][0]
    title = ch["snippet"]["title"]
    print(f"Bağlı kanal: {title}  ({ch['id']})")
    if title != EXPECTED and "--force" not in a:
        sys.exit(f"Beklenen kanal '{EXPECTED}' değil — yanlış hesapla yetki verilmiş olabilir. "
                 "Doğruysa --force ile çalıştır.")
    print("Uygulanacak: banner, açıklama, anahtar kelimeler, çocuklara özel değil, filigran"
          + (f", ülke={country}" if country else ""))
    if "--yes" not in a and input("Devam? [e/H] ").strip().lower() not in ("e", "y", "evet", "yes"):
        sys.exit("iptal")

    # 1) banner → yükle, URL'yi brandingSettings'e yaz
    url = yt.channelBanners().insert(
        media_body=MediaFileUpload(str(HERE / "banner_2560x1440.png"), mimetype="image/png")).execute()["url"]
    b = ch.get("brandingSettings", {})
    b.setdefault("channel", {})
    b["channel"]["description"] = DESCRIPTION
    b["channel"]["keywords"] = " ".join(f'"{k}"' if " " in k else k for k in KEYWORDS)
    b["channel"]["defaultLanguage"] = "en"
    if country:
        b["channel"]["country"] = country
    b.setdefault("image", {})["bannerExternalUrl"] = url
    b.pop("hints", None)
    yt.channels().update(part="brandingSettings", body={"id": ch["id"], "brandingSettings": b}).execute()
    print("✓ banner + açıklama + anahtar kelimeler")

    # 2) kitle: çocuklara özel değil
    yt.channels().update(part="status", body={"id": ch["id"], "status": {"selfDeclaredMadeForKids": False}}).execute()
    print("✓ çocuklara özel değil")

    # 3) filigran (uzun videolarda görünür; Shorts'ta görünmez)
    try:
        yt.watermarks().set(channelId=ch["id"],
                            body={"timing": {"type": "offsetFromStart", "offsetMs": 0},
                                  "position": {"type": "corner", "cornerPosition": "topRight"}},
                            media_body=MediaFileUpload(str(HERE / "watermark_150x150.png"), mimetype="image/png")).execute()
        print("✓ filigran")
    except Exception as e:
        print(f"• filigran atlandı ({str(e)[:120]}) — Studio'dan elle yüklenebilir")

    print("\nElle kalanlar (Studio → Özelleştirme / Ayarlar): profil resmi (brand/profile_800x800.png), "
          "yorum filtresi kelimeleri (brand/KANAL-KURULUM.md), iletişim e-postası.")


if __name__ == "__main__":
    main()

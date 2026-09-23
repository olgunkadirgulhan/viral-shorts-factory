#!/usr/bin/env python3
"""set_trailer.py — Studio'dan elle yüklenen karşılama videosunu kanal fragmanı yapar.
Başlığı "Welcome to Why Stocks Moved" ile başlayan en yeni herkese açık videoyu bulur.

    python brand/set_trailer.py            # otomatik bul
    python brand/set_trailer.py VIDEO_ID   # elle ver
"""
import pathlib, sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))
from common import yt_creds  # noqa: E402

PREFIX = "Welcome to Why Stocks Moved"


def main():
    from googleapiclient.discovery import build
    yt = build("youtube", "v3", credentials=yt_creds(), cache_discovery=False)
    ch = yt.channels().list(part="contentDetails,brandingSettings", mine=True).execute()["items"][0]
    vid = sys.argv[1] if len(sys.argv) > 1 else None
    if not vid:
        uploads = ch["contentDetails"]["relatedPlaylists"]["uploads"]
        ids = [i["contentDetails"]["videoId"] for i in yt.playlistItems().list(
            part="contentDetails", playlistId=uploads, maxResults=50).execute().get("items", [])]
        vids = yt.videos().list(part="snippet,status", id=",".join(ids)).execute().get("items", []) if ids else []
        match = [v for v in vids if v["snippet"]["title"].startswith(PREFIX)]
        if not match:
            sys.exit(f"'{PREFIX}' ile başlayan video bulunamadı — Studio'dan yükledin mi?")
        v = match[0]
        if v["status"]["privacyStatus"] != "public":
            sys.exit(f"Video bulundu ama '{v['status']['privacyStatus']}'. Fragman için Herkese açık olmalı.")
        vid = v["id"]
    b = ch["brandingSettings"]
    b.setdefault("channel", {})["unsubscribedTrailer"] = vid
    b.pop("hints", None)
    yt.channels().update(part="brandingSettings", body={"id": ch["id"], "brandingSettings": b}).execute()
    print(f"✓ kanal fragmanı: https://youtu.be/{vid}")


if __name__ == "__main__":
    main()

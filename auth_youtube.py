#!/usr/bin/env python3
"""auth_youtube.py — tek seferlik YouTube OAuth onayı. Tarayıcı açılır, "İzin ver"e tıkla → state/token.json.
Önce Google Cloud'dan Desktop tipi OAuth client indirip state/client_secret.json olarak kaydet.
"""
import sys

from common import STATE, YT_SCOPES


def main():
    from google_auth_oauthlib.flow import InstalledAppFlow
    secret = STATE / "client_secret.json"
    if not secret.exists():
        sys.exit("state/client_secret.json yok — README'deki 'YouTube OAuth' adımına bak")
    flow = InstalledAppFlow.from_client_secrets_file(str(secret), YT_SCOPES)
    creds = flow.run_local_server(port=0, access_type="offline", prompt="consent")
    (STATE / "token.json").write_text(creds.to_json(), encoding="utf-8")
    from googleapiclient.discovery import build
    ch = build("youtube", "v3", credentials=creds, cache_discovery=False).channels().list(part="snippet", mine=True).execute()
    name = ch["items"][0]["snippet"]["title"] if ch.get("items") else "?"
    print(f"token.json kaydedildi. Bağlı kanal: {name}\n")
    secrets = (("YOUTUBE_CLIENT_ID", creds.client_id), ("YOUTUBE_CLIENT_SECRET", creds.client_secret),
               ("YOUTUBE_REFRESH_TOKEN", creds.refresh_token))
    if "--set-github-secrets" in sys.argv:                  # gh CLI ile doğrudan repoya yaz, ekrana basma
        import subprocess
        for k, v in secrets:
            subprocess.run(["gh", "secret", "set", k, "--body", v], check=True)
        print("GitHub secret'ları yazıldı: " + ", ".join(k for k, _ in secrets))
    else:
        print("GitHub secret'ları (repo → Settings → Secrets and variables → Actions):")
        for k, v in secrets:
            print(f"  {k} = {v}")


if __name__ == "__main__":
    main()

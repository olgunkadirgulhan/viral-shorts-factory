# Viral Shorts Factory: İngilizce, GitHub Actions üzerinde tam otomatik

`gunluk-viral-video-otomasyonu.md` dokümanındaki sistem. **GitHub Actions'ta çalışır, bilgisayarın kapalı olabilir.**
Her gün 10:00 UTC'de (06:00 New York) şu sırayla ilerler:

```
yfinance (gerçek rakamlar) → Reddit talebi → rakip outlier'lar (YouTube API + swipe.py)
→ teardown → hook madenciliği (mine_hooks.py) → fikir havuzu (slot başına 3)
→ hook kapısı (hookscore ≥60) → script + mute kapısı → başlık kapısı (title.py ≥85) → SEO
→ render (renderer.py + edge-tts) → YouTube'a yükleme → state/brain notu → repoya commit → Telegram
```

Kapılardan geçemeyen fikrin yerine sıradaki yedek denenir. Üçü de geçemezse **güvenli format** yüklenir: günün piyasa özeti, LLM kullanmaz. Böylece slot hiç boş kalmaz.

## Dokümandan farkları

| Doküman | Burada | Neden |
|---|---|---|
| n8n cron | **GitHub Actions** (`.github/workflows/`) | Bilgisayar kapalıyken de çalışsın |
| Ollama Llama 3.1 8B | **Claude API** (`claude-opus-5`) | GitHub makinelerinde GPU yok, 8B model orada saatler sürer |
| yt-dlp ile kanal tarama | **YouTube Data API** (kanal başına ~3 birim) | GitHub IP'leri yt-dlp'de bot engeline takılıyor |
| Remotion | `renderer.py` (Pillow + ffmpeg) | Node ya da Chrome gerektirmiyor, aynı props'u okuyor |
| `token.json` diskte | `YOUTUBE_*` secret'ları | Mevcut `crypto-shorts-factory` ile aynı adlar |

## Kurulum (tek sefer)

### 1. Secrets (repo → Settings → Secrets and variables → Actions → Secrets)

| Secret | Zorunlu | Not |
|---|---|---|
| `ANTHROPIC_API_KEY` | evet | crypto-shorts-factory'deki anahtarı kullanabilirsin |
| `YOUTUBE_CLIENT_ID` / `YOUTUBE_CLIENT_SECRET` / `YOUTUBE_REFRESH_TOKEN` | evet | Aşağıdaki 2. adıma bak |
| `TELEGRAM_BOT_TOKEN` / `TELEGRAM_CHAT_ID` | hayır | Günlük rapor için |

### 2. YouTube yetkisi

Google Cloud'da **YouTube Data API v3** ve **YouTube Analytics API** açık olmalı. Bir Desktop OAuth client oluştur, JSON'unu `state\client_secret.json` olarak kaydet. Bu dosya git'e girmez. Sonra bu klasörde:

```powershell
python auth_youtube.py --set-github-secrets
```

Tarayıcıda kanalın hesabını seçip "İzin ver"e tıkla. Üç YouTube secret'ı doğrudan repoya yazılır. Mevcut projenin refresh token'ını da kullanabilirsin, ama haftalık analiz Analytics yetkisi ister. O yüzden bu betikle yeni bir token üret.

**OAuth consent screen → Publish app ("In production")** yap, yoksa token 7 günde düşer. Herkese açık yayın için **YouTube API audit** formunu da doldur.

### 3. Variables (aynı sayfa → Variables sekmesi, hepsi opsiyonel)

| Variable | Varsayılan | Not |
|---|---|---|
| `YOUTUBE_PRIVACY` | `unlisted` | İlk hafta izle. Sonra `scheduled` yap: video slot saatinde herkese açılır |
| `VIDEOS_PER_DAY` | `2` | Günlük kota ~6 video. crypto-shorts-factory aynı Google projesindeyse toplamı hesapla |
| `SLOTS` | `12:30=SHARE,19:00=SAVE,17:00=FOLLOW` | New York saati. Kripto kanalının 09/14/19 UTC slotlarıyla çakışmaz |
| `ANTHROPIC_MODEL` | `claude-opus-5` | Ucuzlatmak için `claude-haiku-4-5` |
| `MARKET_TICKERS` | `BTC-USD,ETH-USD,^GSPC,^IXIC,GC=F,CL=F,NVDA,TSLA` | Yahoo Finance sembolleri |
| `CHANNEL_NAME`, `TTS_VOICE` | — / `en-US-AndrewMultilingualNeural` | |

### 4. Rakip kanallar

`state/channels.txt` dosyasına 10-20 rakip kanalın `@handle/shorts` URL'sini yazıp commit'le. Liste boşken sistem sadece piyasa özeti yükler.

### 5. Test

Actions → **Daily viral short** → Run workflow. `dry_run` varsayılan olarak açık. Videolar run sayfasında artifact olarak iner. Sorun yoksa cron'a bırak.

## Takvim (UTC)

| Workflow | Ne zaman | Ne yapar |
|---|---|---|
| Daily viral short | her gün 10:00 | Üretim ve yükleme. `state/`, `data/outliers_*`, `data/job_*` commit'lenir |
| Weekly review | Pazartesi 02:00 (Pazar 22:00 NY) | Retention, audit, trend ve yorumlar → `state/lessons.md` |

Her çalışma yt-dlp'yi, iki skill reposunu ve edge-tts'i en güncel haliyle kurar. Ayrı bir güncelleme işi yok. Her gün commit düştüğü için GitHub cron'u 60 gün sonra kapatmaz.

## Maliyet

- **Claude:** Video başına ~10-15 çağrı var ve SKILL.md dosyaları sistem mesajı olarak gidiyor. Kabaca 30-80k girdi ve 8-15k çıktı token'ı eder; yeniden deneme sayısına göre değişir. Opus 5 ile video başına ~$0.35-0.75, günde 2 videoda ayda ~$20-45. `claude-haiku-4-5` ile bunun ~1/5'i.
- **GitHub Actions:** Çalışma başına ~10-20 dk. Private repoda ayda 2.000 dk ücretsiz ve crypto-shorts-factory de bu havuzdan ~1.080 dk yiyor. Sınıra yaklaşırsan repoyu public yap. Secret'lar public repoda da gizli kalır.
- **YouTube kotası:** Yükleme başına ~1.600 birim, keşif ~60 birim.

## Yerelde çalıştırma

```powershell
powershell -ExecutionPolicy Bypass -File setup.ps1
python daily_viral.py --videos 1 --dry-run          # .env'e ANTHROPIC_API_KEY yaz
python daily_viral.py --fallback-only --dry-run     # LLM'siz, sadece piyasa özeti
```

`CONTENT_LANG=tr` yaparsan tüm sistem Türkçe çalışır: TTS, ekran yazıları ve Türkçe sözlüklü hook/başlık kapıları.

# Günlük Viral Video Otomasyonu — 2 skill paketi, tek pipeline

> **Kaynak 1:** [Jakeschincariol/youtube-agent-skill](https://github.com/Jakeschincariol/youtube-agent-skill): 11 YouTube skill'i ve 6 Python aracı (MIT, bağımlılık yok). Güçlü yanı **ölçüm**: outlier, hook ve başlık puanlaması, izleyici kaybı (retention) analizi.
> **Kaynak 2:** [Ootto-AI/claude-content-skills](https://github.com/Ootto-AI/claude-content-skills): 50+ kısa video skill'i ve `mine_hooks.py` (MIT). Güçlü yanı **üretim**: viral stratejisi, videoyu parça parça inceleme (teardown), hook remix, ekran yazıları, platforma uyarlama.
> **Hedef:** Her gün **nişte o an patlayan videoları bul → yapısını incele → kendi orijinal videonu üret → puanlarla kontrol et → render et → YouTube Shorts'a yükle**. Manuel adım yok.
> **Kapsam:** Sadece YouTube. TikTok ve IG Reels sonraki aşamada eklenecek (bkz. §10).
> **Stack:** n8n + yfinance + Ollama (Llama 3.1 8B) + Remotion + YouTube Data API (mevcut sistemin).

---

## 0. Önemli: İki repo da tek başına "tam otomatik" değil

- youtube-agent-skill: *"Nothing gets published until you do it"*. Her skill **"ship it, or change it?"** sorusuyla biter.
- Ootto content-factory: "pausing for your go-ahead at the steps that matter (the format pick, and before posting)". Paylaşmadan önce onay bekler.

Bu dokümanda o insan onaylarının yerine **sayısal otomatik kapılar** koyuyoruz:

| Repo'daki insan kararı | Bizim otomatik kapımız |
|---|---|
| "Hangi viral formatı modelleyelim?" (Ootto) | `swipe.py` multiple **≥ 3.0x** olan en üst outlier |
| "10 hook'tan birini seç" (Ootto viral-hook-writer) | 10 hook → `hookscore.py`, en yüksek **verdict ≥ 60**, yoksa yeniden üret (max 3) |
| "Başlık/thumbnail tamam mı?" (yt-package) | `title.py` score **≥ 85** ve `issues` boş |
| "Sessizde anlaşılıyor mu?" (Ootto on-screen-text) | Mute pass: ekran yazısı satırları ≤ 7 kelime, hepsi dolu |
| "Ship it?" / "Post after my OK" | Tüm kapılar geçtiyse otomatik upload. Geçmediyse **sıradaki yedek fikir** denenir (slot başına 3 fikir). O da olmazsa slot boş kalmaz, **güvenli format** (günün piyasa özeti) yüklenir |

### Senin hiçbir şey yapmadığın kısım (her gün, her hafta)

Keşif, fikir, script, render, yükleme, zamanlı yayın, haftalık analiz ve öğrenme tamamen otomatik. Hata olursa sistem kendi toparlar:

| Durum | Otomatik tepki |
|---|---|
| Kontrol puanı tutmadı | Aynı slot için sıradaki yedek fikir (3'e kadar) |
| 3 fikir de tutmadı | Güvenli format: günün piyasa özeti (mevcut recap template'i) yüklenir, slot boş kalmaz |
| Bugün 3x outlier yok | Eşik 2x'e düşer; yine yoksa son 7 günün outlier'ları kullanılır |
| Ağ, Ollama ya da render hatası | 3 kez tekrar dener (30 sn, 2 dk, 5 dk bekleyerek) |
| OAuth token süresi doldu | Otomatik yenilenir ve diske yazılır |
| yt-dlp YouTube değişikliğinde bozuldu | Her pazartesi otomatik güncellenir |

Telegram mesajları sadece bilgi içindir; hiçbirine cevap vermen gerekmez.

### Sadece bir kez yapılacak 3 insan adımı (kurulumda)

Bunlar Google'ın kuralı, kodla atlanamaz:

1. **OAuth onayı:** İlk çalıştırmada tarayıcıda bir kez "İzin ver"e tıklanır.
2. **OAuth uygulamasını "In production" yap:** Google Cloud → OAuth consent screen → *Publish app*. "Testing" modunda kalırsa token 7 günde bir düşer ve sistem durur.
3. **YouTube API audit başvurusu:** Denetimden geçmemiş projelerin yüklediği videolar gizli (private) kalır. Form bir kez doldurulur. Onay gelene kadar sistem yine her şeyi üretip yükler, videolar sadece gizli durur.

Bu üçü bittikten sonra sisteme dokunman gerekmez.

---

## 1. Hangi skill nerede? (iki repo birleşik)

### Günlük pipeline'da çalışanlar

| Adım | Skill (repo) | Araç | Görevi |
|---|---|---|---|
| 1. Talep | `agent-reach` (Ootto) | Reddit public JSON | Nişteki subreddit'lerde bugün en çok konuşulan sorular → konu havuzu |
| 2. Keşif | `/yt-viral` (YT) | `swipe.py` | Rakiplerde kendi kanal medyanının 3x+ üstüne çıkan videolar |
| 3. İnceleme | `reel-analyzer` + `agent-reach` video (Ootto) | `yt-dlp` altyazı | En iyi outlier'ın transkripti → hook, beat yapısı, tempo, görsel teknik |
| 4. Strateji | `going-viral` (Ootto) | — | Slot başına TEK hedef: SAVE / SHARE / FOLLOW → duygu → açı |
| 5. Hook madenciliği | `hook-mining` (Ootto) | `mine_hooks.py` | Outlier başlıklarını psikolojik kalıba göre grupla, güçlü kelimeleri çıkar |
| 6. Hook yazımı | `viral-hook-writer` (Ootto) + `/yt-script` (YT) | `hookscore.py` | Yapı aynı kalır, sadece güçlü kelimeler değişir → 10 hook → puan kapısı |
| 7. Script | `reel-scripter` + `reel-builder` (Ootto), `/yt-shorts` (YT) | — | 25-40 sn orijinal script, her beat'te görsel, loop noktası, sonda bekletilen payoff |
| 8. Ekran yazısı | `on-screen-text-writer` (Ootto) | mute kapısı | Beat başına ≤7 kelime başlık, vurgulanacak kelime |
| 9. Paket | `/yt-package` (YT) + `cover-thumbnail-brief` (Ootto) | `title.py` | 10 başlık+kapak metni → lint → kapak görseli brief'i |
| 10. SEO | `/yt-seo` (YT) | — | Açıklamanın ilk 2 satırı, en fazla 15 tag, 3 hedef arama sorgusu testi |
| 11. Hafıza | `ai-brain` (Ootto) | Obsidian uyumlu `.md` | Kazanan hook/format notu → sonraki üretimler okur |

### Haftalık / aylık çalışanlar

| Sıklık | Skill (repo) | Görevi |
|---|---|---|
| Pazar | `/yt-retention` (YT) + `retention.py` | Analytics API'den izleyici kaybı → `lessons.md` |
| Pazar | `content-audit` (Ootto) | Son 30 video: kendi medyana göre multiple → **STOP / KEEP / TEST** listeleri |
| Pazar | `trend-spotter` (Ootto) | Nişte yükselen formatlar: **TAKE IT / ADAPT IT / SIT IT OUT** |
| Pazar | `comment-mining` (Ootto) | Kendi yorumlarından sorular → sonraki haftanın fikir havuzu |
| Pazar | `/yt-plan` (YT) + `best-time-scheduler` (Ootto) | Slot saatleri kendi verinden (yoksa "hipotez" etiketiyle) |
| Aylık | `/yt-audit` (YT) | Kanal geneli TEK düzeltme |

### Kullanılmayanlar ve nedenleri

- `caption-and-hashtags`, `cross-platform-reformatter`: TikTok/IG içindir, ikinci aşamaya bırakıldı (§10).
- `comment-responder`, `dm-script-writer`: YouTube'da DM yok. Ayrıca otomatik DM finans nişinde spam ve uyum riski taşıyor.
- `/yt-comment`: Otomatik yorum cevabı spam riski taşıyor.
- `/yt-edit`, `/yt-chapters`, `b-roll-shot-list`, `ugc-creator-brief`: Konuşan kafa ya da çekim içindir. Remotion ile üretilen Shorts'ta gereksiz.
- `carousel-builder`, `story-sequencer`, `x-thread-strategy`, `linkedin-*`, `paid-social-brief`, `influencer-*`, `collab-outreach`, `creator-outreach`, `utm-campaign-plan` vb.: Video pipeline'ının kapsamı dışında.
- `content-factory` (Ootto orkestratörü): **Mantığı birebir alındı** ama Apify/Composio yerine kendi araçlarımızla çalışıyor. Bu dokümandaki `daily_viral.py`, content-factory'nin otomatik versiyonu.

---

## 2. Kurulum (tek sefer, ~25 dk)

```bash
# 1) İki repo
cd /opt
git clone https://github.com/Jakeschincariol/youtube-agent-skill.git
git clone https://github.com/Ootto-AI/claude-content-skills.git
export YTS=/opt/youtube-agent-skill/skills
export OOT=/opt/claude-content-skills/skills

# 2) Araçlar
pip install -U yt-dlp google-api-python-client google-auth-oauthlib requests --break-system-packages

# 3) Çalışma klasörü (state/brain = Obsidian vault'u olarak da açılabilir)
mkdir -p /opt/viral/{data,out,state/brain}
cd /opt/viral
cp $YTS/../templates/voice.md state/voice.md   # doldur (bkz. §3)
touch state/lessons.md
```

**`state/channels.txt`**: Nişindeki rakip kanallar (10-20 tane, her birinden en az 4 video olmalı):
```
https://www.youtube.com/@kanal1/shorts
https://www.youtube.com/@kanal2/shorts
```

**`state/subreddits.txt`**: Talep sinyali (agent-reach mantığı):
```
stocks
investing
CryptoCurrency
wallstreetbets
```

**YouTube OAuth** (bir kez): Google Cloud'da YouTube Data API v3 ve YouTube Analytics API'yi aç, Desktop tipinde OAuth client oluştur, `state/client_secret.json` olarak kaydet. İlk çalıştırmada `state/token.json` oluşur.

> İstersen `bash /opt/claude-content-skills/install.sh` ile tüm skill'ler `~/.claude/skills/`'e de kurulur ve Claude Code'da elle `/reel-analyzer` gibi çağırabilirsin. Pipeline buna ihtiyaç duymuyor, SKILL.md'leri doğrudan okuyor.

---

## 3. `voice.md` ve `brain/`: sistemin kişiliği ve hafızası

`voice.md` (YT repo şablonu), finans kanalı için:

```markdown
## Who I am talking to
25-40 yaşında, borsa/kripto takip eden ama grafik okumayı bilmeyen, günde 5 dk ayıran biri.

## Words I never use
"anlık" (veri 15 dk gecikmeli), "kesin", "garanti", "uçacak", "game-changer", "let's dive in"

## What I will not claim
Fiyat tahmini, al/sat tavsiyesi, elimde olmayan rakam. Her videoda "Yatırım Tavsiyesi Değildir".

## My format
25-40 sn dikey. Hook ilk 1.5 sn'de oturur, frame 0'da hareketli grafik. Her zaman grafik.
Kanal intro yok. Tek CTA sonda. Sessizde anlaşılır (ekran yazısı her beat'te).
```

`state/brain/` (Ootto `ai-brain` mantığı): Her yayınlanan video için `YYYY-MM-DD-slug.md` notu ve `MOC.md` indeksi. Pipeline her sabah sadece **son 10 notu ve lessons.md'yi** okur, token maliyeti düşük kalır. Klasörü Obsidian'da vault olarak açarsan graf görünümünü de alırsın.

---

## 4. Günlük akış (tam otomatik)

```
06:00  TALEP      Reddit top/day (subreddits.txt)          → demand.json         [agent-reach]
06:02  KEŞİF      yt-dlp kanallar → swipe.py --min 3        → outliers.json       [yt-viral]
06:04  İNCELEME   #1 outlier altyazısı → teardown            → teardown.json       [reel-analyzer]
06:05  MADENCİLİK outlier başlıkları CSV → mine_hooks.py     → hooks.mined.json    [hook-mining]
06:06  SEÇİM      outlier + teardown + talep + yfinance → N fikir, her slota hedef  [going-viral]
       ─── her fikir için ───
       HOOK       10 hook (remix) → hookscore.py → kapı ≥60                        [viral-hook-writer + yt-script]
       SCRIPT     25-40 sn, beat + görsel + loop + payoff                          [reel-scripter/builder + yt-shorts]
       EKRAN      beat başına ≤7 kelime → mute kapısı                              [on-screen-text-writer]
       PAKET      10 başlık+kapak → title.py → kapı ≥85 → kapak brief'i            [yt-package + cover-brief]
       SEO        YT açıklama/tag + 3 sorgu testi                                  [yt-seo]
       RENDER     Remotion (mevcut template) + TTS
       YÜKLEME    YouTube: videos.insert + publishAt (zamanlı yayın)
       HAFIZA     brain/ notu + MOC                                                 [ai-brain]
       ──────────────────
       YEDEK      Kontrol tutmazsa → sıradaki fikir (3'e kadar) → yine olmazsa güvenli piyasa özeti
       LOG        Telegram özeti (sadece bilgi, işlem gerekmez)
```

Slot hedefleri `going-viral` rotasyonuna göre: **14:00 → SHARE** (öfke/hayret: "bunu bilmeyen kaybediyor"), **20:00 → SAVE** (numaralı sistem: "kaydet, lazım olacak"), üçüncü slot açılırsa **FOLLOW**.

---

## 5. Orkestratör: `daily_viral.py`

Tek dosya. n8n sadece bunu tetikler (`Execute Command` node). LLM olarak yerel **Ollama** kullanılır, token maliyeti sıfır. Her adımın prompt'u ilgili **SKILL.md'yi sistem mesajı olarak** kullanır, yani repo'lardaki kurallar birebir uygulanır.

```python
#!/usr/bin/env python3
"""daily_viral.py — youtube-agent-skill + claude-content-skills → tam otomatik günlük pipeline.
Kullanım: python3 daily_viral.py --videos 2
"""
import csv, glob, json, os, re, subprocess, sys, datetime, pathlib, requests

YTS  = os.environ.get("YTS", "/opt/youtube-agent-skill/skills")
OOT  = os.environ.get("OOT", "/opt/claude-content-skills/skills")
BASE = pathlib.Path("/opt/viral")
DATA, OUT, STATE = BASE/"data", BASE/"out", BASE/"state"
BRAIN = STATE/"brain"
REMOTION_DIR = os.environ.get("REMOTION_DIR", "/opt/finans-shorts/remotion")
OLLAMA = os.environ.get("OLLAMA_URL", "http://localhost:11434/api/generate")
MODEL  = os.environ.get("OLLAMA_MODEL", "llama3.1:8b")
TG_TOKEN, TG_CHAT = os.environ.get("TG_TOKEN"), os.environ.get("TG_CHAT")

HOOK_MIN, TITLE_MIN, OUTLIER_MIN, MAX_TRIES, MAX_OSD_WORDS = 60, 85, 3.0, 3, 7
TODAY = datetime.date.today().isoformat()
SLOTS = [("11:00:00Z", "SHARE"), ("17:00:00Z", "SAVE"), ("08:00:00Z", "FOLLOW")]  # UTC (İstanbul -3)

# ---------------- yardımcılar ----------------
def sh(cmd, cwd=None):
    return subprocess.run(cmd, capture_output=True, text=True, check=True, cwd=cwd).stdout

def skill(repo, name):
    root = YTS if repo == "yt" else OOT
    return (pathlib.Path(root)/name/"SKILL.md").read_text()

def context():
    voice = (STATE/"voice.md").read_text()
    lessons = (STATE/"lessons.md").read_text() if (STATE/"lessons.md").exists() else ""
    notes = sorted(glob.glob(str(BRAIN/"20*.md")))[-10:]            # ai-brain: sadece son 10 not
    brain = "\n---\n".join(pathlib.Path(n).read_text()[:600] for n in notes)
    return f"VOICE PROFILE:\n{voice}\n\nLESSONS (our retention data):\n{lessons}\n\nPAST WINNERS (ai-brain):\n{brain}"

def llm(system, prompt, as_json=True):
    r = requests.post(OLLAMA, json={
        "model": MODEL, "system": system, "prompt": prompt, "stream": False,
        **({"format": "json"} if as_json else {}), "options": {"temperature": 0.8, "num_ctx": 8192}
    }, timeout=600)
    txt = r.json()["response"]
    return json.loads(txt) if as_json else txt

def retry(fn, *a, tries=3, waits=(30, 120, 300), **kw):
    import time
    for k in range(tries):
        try:
            return fn(*a, **kw)
        except Exception as e:
            if k == tries - 1: raise
            print(f"retry {fn.__name__} ({e}) in {waits[k]}s"); time.sleep(waits[k])

def yt_creds():
    from google.oauth2.credentials import Credentials
    from google.auth.transport.requests import Request
    tok = STATE/"token.json"
    creds = Credentials.from_authorized_user_file(str(tok))
    if not creds.valid and creds.refresh_token:
        creds.refresh(Request()); tok.write_text(creds.to_json())   # otomatik yenile + kaydet
    return creds

def tg(msg):
    if TG_TOKEN:
        requests.post(f"https://api.telegram.org/bot{TG_TOKEN}/sendMessage",
                      json={"chat_id": TG_CHAT, "text": msg[:4000]})

# ---------------- 1. TALEP (agent-reach → Reddit) ----------------
def demand():
    out = []
    for sub in (STATE/"subreddits.txt").read_text().split():
        try:
            j = requests.get(f"https://www.reddit.com/r/{sub}/top.json?t=day&limit=15",
                             headers={"User-Agent": "viral-pipeline/1.0"}, timeout=20).json()
            out += [{"sub": sub, "title": c["data"]["title"], "score": c["data"]["score"],
                     "comments": c["data"]["num_comments"]} for c in j["data"]["children"]]
        except Exception as e:
            print("reddit skip", sub, e)
    out.sort(key=lambda x: -(x["score"] + 3 * x["comments"]))
    return out[:20]

# ---------------- 2. KEŞİF (/yt-viral) ----------------
def discover():
    rows = []
    for url in (STATE/"channels.txt").read_text().split():
        try:
            j = json.loads(sh(["yt-dlp", "--flat-playlist", "-J", "--playlist-end", "30", url]))
        except Exception as e:
            print("skip", url, e); continue
        ch = j.get("channel") or j.get("uploader") or url
        for e in j.get("entries", []):
            if e.get("view_count"):
                rows.append({"channel": ch, "title": e.get("title", ""), "views": e["view_count"],
                             "duration": e.get("duration"),
                             "url": e.get("url") or f"https://www.youtube.com/shorts/{e.get('id')}"})
    p = DATA/f"collected_{TODAY}.json"; p.write_text(json.dumps(rows))
    for lo in (OUTLIER_MIN, 2.0):                                  # eşik düşürme yedeği
        res = json.loads(sh(["python3", f"{YTS}/yt-viral/swipe.py", str(p), "--min", str(lo), "--json"]))
        if res["outliers"]: break
    if not res["outliers"]:                                        # son 7 günün outlier'ları
        for f in sorted(glob.glob(str(DATA/"outliers_*.json")))[-7:]:
            res["outliers"] += json.load(open(f))["outliers"][:5]
        res["outliers"].sort(key=lambda r: -r["multiple"])
    (DATA/f"outliers_{TODAY}.json").write_text(json.dumps(res, indent=1))
    return res["outliers"]

# ---------------- 3. İNCELEME (reel-analyzer + agent-reach video) ----------------
def transcript(url):
    stem = DATA/f"sub_{TODAY}"
    try:
        sh(["yt-dlp", "--write-auto-sub", "--write-sub", "--sub-lang", "en.*,tr", "--sub-format", "vtt",
            "--skip-download", "-o", str(stem), url])
    except Exception:
        return ""
    files = glob.glob(f"{stem}*.vtt")
    if not files: return ""
    lines, seen = [], set()
    for ln in open(files[0], encoding="utf-8", errors="ignore"):
        ln = re.sub(r"<[^>]+>", "", ln).strip()
        if not ln or "-->" in ln or ln.startswith(("WEBVTT", "Kind:", "Language:")) or ln in seen: continue
        seen.add(ln); lines.append(ln)                    # auto-sub tekrarlarını ayıkla
    for f in files: os.remove(f)
    return " ".join(lines)[:4000]

def teardown(outlier):
    t = transcript(outlier["url"])
    return llm(skill("oot", "reel-analyzer") + "\n\n" + context(),
        f"""Reel to model: "{outlier['title']}" ({outlier['multiple']}x its channel median, formula: {outlier['formula']}).
Transcript: {t or "(no transcript available — work from title + formula only, say so)"}
Return JSON: {{"hook":"...","hook_why":"...","beats":[{{"t":"0-3s","said":"...","shown":"..."}}],
"pacing":"...","visual_technique":"...","reusable_moves":["...","..."],"remake_plan":"..."}}
Model the TECHNIQUE, never reproduce the creator's words.""")

# ---------------- 4. HOOK MADENCİLİĞİ (hook-mining) ----------------
def mine(outliers):
    p = DATA/f"hooks_{TODAY}.csv"
    with open(p, "w", newline="") as f:
        w = csv.writer(f); w.writerow(["hook", "score"])
        for o in outliers: w.writerow([o["title"], o["multiple"]])     # performans = kendi medyanına göre multiple
    sh(["python3", f"{OOT}/hook-mining/mine_hooks.py", str(p), "--top", "40"])
    return json.loads((DATA/f"hooks_{TODAY}.mined.json").read_text())

# ---------------- 5. SEÇİM + STRATEJİ (going-viral) ----------------
def pick_ideas(outliers, td, dem, market, goals):
    return llm(skill("oot", "going-viral") + "\n\n" + skill("yt", "yt-viral") + "\n\n" + context(),
        f"""Top outliers: {json.dumps(outliers[:5], ensure_ascii=False)}
Teardown of #1: {json.dumps(td, ensure_ascii=False)}
What people ask today (Reddit): {json.dumps(dem[:10], ensure_ascii=False)}
Today's REAL market data (only these numbers, never invent): {json.dumps(market, ensure_ascii=False)}
Make {len(goals)} ideas. Idea i has goal = {goals}[i]. Each reuses a proven STRUCTURE on today's data,
answers a real audience question where possible, and states the emotion that drives its goal.
JSON: {{"ideas":[{{"idea":"...","goal":"SHARE|SAVE|FOLLOW","emotion":"...","formula":"...",
"structure_from":"<outlier url>","payoff_withheld_until_end":"...","data_points":["..."]}}]}}""")["ideas"][:len(goals)]

# ---------------- 6. HOOK (viral-hook-writer + hook-mining remix) → hookscore kapısı ----------------
def best_hook(idea, mined):
    buckets = {k: [h["hook"] for h in v[:3]] for k, v in mined["buckets"].items()}
    for _ in range(MAX_TRIES):
        hooks = llm(skill("oot", "viral-hook-writer") + "\n\n" + skill("oot", "hook-mining") + "\n\n"
                    + skill("yt", "yt-script") + "\n\n" + context(),
            f"""Idea: {json.dumps(idea, ensure_ascii=False)}
Proven hook skeletons in our niche (by pattern): {json.dumps(buckets, ensure_ascii=False)}
Power words earning their keep: {mined['power_word_frequency'][:15]}
Write 10 hooks (<12 words, spoken). At least 5 are REMIXES: keep a proven skeleton, swap ONLY power words,
never verbatim. Use real numbers from the idea only. Each has a 3-5 word on-screen version.
JSON: {{"hooks":[{{"line":"...","on_screen":"...","pattern":"..."}}]}}""")["hooks"]
        f = DATA/"hooks.txt"; f.write_text("\n".join(h["line"].replace("\n", " ") for h in hooks))
        scored = json.loads(sh(["python3", f"{YTS}/yt-script/hookscore.py", "--json", str(f)]))
        by_line = {h["line"].replace("\n", " "): h for h in hooks}
        scored.sort(key=lambda x: -x["verdict"])
        top = scored[0]
        if top["verdict"] >= HOOK_MIN:
            return {**top, "on_screen": by_line.get(top["hook"], {}).get("on_screen", "")}
    return None

# ---------------- 7-8. SCRIPT + EKRAN YAZISI (reel-scripter/builder, yt-shorts, on-screen-text) ----------------
def write_script(idea, hook, td):
    s = llm(skill("oot", "reel-scripter") + "\n\n" + skill("oot", "reel-builder")[:3000] + "\n\n"
            + skill("yt", "yt-shorts") + "\n\n" + skill("oot", "on-screen-text-writer") + "\n\n" + context(),
        f"""Idea: {json.dumps(idea, ensure_ascii=False)}
Winning hook (first spoken line, verbatim): {hook['hook']}   On-screen at frame 0: {hook['on_screen']}
Structure to model (NOT words): {json.dumps(td.get('beats', []), ensure_ascii=False)} · pacing: {td.get('pacing','')}
Write a 25-40s vertical Short (75-100 words). Frame 0 = moving chart. Claim lands ~1.5s.
Re-hook at ~9s and ~15s. Tease the payoff in the hook, deliver it in the LAST beat.
Every beat: spoken line + on-screen text (headline, <=7 words, one EMPHASIS word) + visual for Remotion.
Last line loops into the first. One CTA. Final beat on-screen: "Yatırım Tavsiyesi Değildir".
JSON: {{"beats":[{{"say":"...","osd":"...","emphasis":"...","visual":"chart|counter|list|compare|text"}}],"word_count":0}}""")
    s["mute_pass"] = all(b.get("osd") and len(b["osd"].split()) <= MAX_OSD_WORDS for b in s["beats"])
    return s

# ---------------- 9. PAKET (yt-package + cover-thumbnail-brief) → title.py kapısı ----------------
def package(idea, script):
    for _ in range(MAX_TRIES):
        cand = llm(skill("yt", "yt-package") + "\n\n" + skill("oot", "cover-thumbnail-brief") + "\n\n" + context(),
            f"""Idea: {idea['idea']}  Hook: {script['beats'][0]['say']}
TEN title+cover pairs. Title <=60 chars (ideally <=40), carries a number/name/date from the idea.
Cover text max 3 words, different words from title, legible at 150px, clear of top 12% / bottom 20%.
JSON: {{"pairs":[{{"title":"...","thumb":"...","visual_brief":"..."}}]}}""")["pairs"]
        best = None
        for c in cand:
            r = json.loads(sh(["python3", f"{YTS}/yt-package/title.py", "--title", c["title"],
                               "--thumb", c["thumb"], "--json"]))[0]
            if not best or r["score"] > best["score"]:
                best = {**r, "thumb": c["thumb"], "visual_brief": c.get("visual_brief", "")}
        if best["score"] >= TITLE_MIN and not best["issues"]:
            return best
    return None

# ---------------- 10. SEO (yt-seo) ----------------
def seo(idea, pkg, script):
    s = llm(skill("yt", "yt-seo") + "\n\n" + context(),
        f"""Title: {pkg['title']}  Idea: {idea['idea']}  Goal: {idea['goal']}
Script: {json.dumps(script['beats'], ensure_ascii=False)}
JSON: {{
 "youtube": {{"queries":["q1","q2","q3"],"description":"2 lines = what viewer gets, then 'Yatırım Tavsiyesi Değildir', then #shorts","tags":["<=15"]}}
}}""")
    yt = s["youtube"]; yt["tags"] = yt["tags"][:15]
    head = (pkg["title"] + " " + yt["description"][:200]).lower()
    yt["query_test_pass"] = any(all(w in head for w in q.lower().split()[:2]) for q in yt["queries"])
    return s

# ---------------- RENDER + YÜKLEME ----------------
def render(job, i):
    props = OUT/f"{TODAY}_{i}.json"; props.write_text(json.dumps(job, ensure_ascii=False))
    mp4 = OUT/f"{TODAY}_{i}.mp4"
    sh(["npx", "remotion", "render", "src/index.ts", "FinanceShort", str(mp4), f"--props={props}"], cwd=REMOTION_DIR)
    return mp4

def upload_youtube(mp4, pkg, yt, publish_at):
    from googleapiclient.discovery import build
    from googleapiclient.http import MediaFileUpload
    api = build("youtube", "v3", credentials=yt_creds())
    body = {"snippet": {"title": pkg["title"], "description": yt["description"], "tags": yt["tags"], "categoryId": "25"},
            "status": {"privacyStatus": "private", "publishAt": publish_at, "selfDeclaredMadeForKids": False}}
    return api.videos().insert(part="snippet,status", body=body,
                               media_body=MediaFileUpload(str(mp4), resumable=True)).execute()["id"]

# ---------------- 12. HAFIZA (ai-brain) ----------------
def brain_save(job):
    slug = re.sub(r"[^a-z0-9]+", "-", job["package"]["title"].lower())[:40].strip("-")
    name = f"{TODAY}-{slug}"
    (BRAIN/f"{name}.md").write_text(f"""# Video — {TODAY} — {job['package']['title']}
#ai-brain #video #{job['idea']['goal'].lower()} #{job['hook']['formula'].lower().replace(' ', '-')}
Related:: [[MOC]]
## Decisions
- Goal {job['idea']['goal']} / emotion {job['idea'].get('emotion','')} — structure from {job['idea'].get('structure_from','')}
- Hook ({job['hook']['verdict']}): {job['hook']['hook']}
- Title ({job['package']['score']}): {job['package']['title']} · cover "{job['package']['thumb']}"
## Built
- youtu.be/{job.get('video_id','')}
## Open
- [ ] Pazar retention sonucu → lessons.md
""")
    with open(BRAIN/"MOC.md", "a") as f:
        f.write(f"- [[{name}]] — {job['idea']['goal']} · hook {job['hook']['verdict']}\n")

# ---------------- MAIN ----------------
def main():
    n = int(sys.argv[sys.argv.index("--videos") + 1]) if "--videos" in sys.argv else 2
    slots = SLOTS[:n]
    market = json.loads(sh(["python3", str(BASE/"market_snapshot.py")]))   # mevcut yfinance script'in
    dem = retry(demand)
    outliers = retry(discover)
    td = retry(teardown, outliers[0]) if outliers else {}
    mined = mine(outliers) if outliers else {"buckets": {}, "power_word_frequency": []}
    goals = [g for _, g in slots]
    # slot başına 3 aday fikir (1 asıl + 2 yedek)
    pool = retry(pick_ideas, outliers, td, dem, market, goals * 3) if outliers else []
    report = []
    for i, (slot_time, goal) in enumerate(slots):
        publish_at = f"{TODAY}T{slot_time}"
        done = False
        for idea in [x for x in pool if x.get("goal") == goal][:3] or pool[i::len(slots)][:3]:
            try:
                job = produce(idea, mined, td)
                if not job:
                    report.append(f"↻ {idea['idea'][:40]} — kontrolü geçemedi, yedeğe geçildi"); continue
                mp4 = retry(render, job, i)
                job["video_id"] = retry(upload_youtube, mp4, job["package"], job["platforms"]["youtube"], publish_at)
                (DATA/f"job_{TODAY}_{i}.json").write_text(json.dumps(job, ensure_ascii=False, indent=1))
                brain_save(job)
                report.append(f"✅ [{goal}] {job['package']['title']}\n   hook {job['hook']['verdict']} · title {job['package']['score']}\n   https://youtu.be/{job['video_id']}")
                done = True; break
            except Exception as e:
                report.append(f"↻ {idea['idea'][:40]} — hata: {e}")
        if not done:                                               # slot asla boş kalmaz
            vid = retry(fallback_recap, market, i, publish_at)
            report.append(f"🛟 [{goal}] güvenli format (piyasa özeti) yüklendi → https://youtu.be/{vid}")
    tg(f"🎬 {TODAY} günlük viral (bilgi amaçlı, işlem gerekmez)\n\n" + "\n\n".join(report))

def produce(idea, mined, td):
    hook = best_hook(idea, mined)
    if not hook: return None
    script = write_script(idea, hook, td)
    if not script["mute_pass"]: return None
    pkg = package(idea, script)
    if not pkg: return None
    return {"idea": idea, "hook": hook, "script": script, "package": pkg,
            "platforms": {"youtube": seo(idea, pkg, script)["youtube"]}, "teardown": td}

def fallback_recap(market, i, publish_at):
    """Mevcut finans pipeline'ının günlük recap template'i — LLM puan kapısına bağlı değil."""
    props = OUT/f"{TODAY}_fallback_{i}.json"; props.write_text(json.dumps({"market": market}, ensure_ascii=False))
    mp4 = OUT/f"{TODAY}_fallback_{i}.mp4"
    sh(["npx", "remotion", "render", "src/index.ts", "DailyRecap", str(mp4), f"--props={props}"], cwd=REMOTION_DIR)
    title = f"Piyasa Özeti {datetime.date.today():%d.%m.%Y}"
    yt = {"description": "Günün piyasa özeti.\nYatırım Tavsiyesi Değildir.\n#shorts", "tags": ["borsa", "piyasa", "kripto"]}
    return upload_youtube(mp4, {"title": title}, yt, publish_at)

if __name__ == "__main__":
    main()
```

---

## 6. Haftalık öğrenme döngüsü: `weekly_review.py`

Her Pazar 4 skill çalışır, çıktıları `lessons.md` dosyasına yazılır. Sonraki haftanın her prompt'u bu dosyayı okur.

```python
#!/usr/bin/env python3
"""weekly_review.py — yt-retention + content-audit + trend-spotter + comment-mining + best-time-scheduler"""
import json, glob, subprocess, pathlib, datetime, requests, os, statistics
from googleapiclient.discovery import build
from google.oauth2.credentials import Credentials

YTS = os.environ.get("YTS", "/opt/youtube-agent-skill/skills")
OOT = os.environ.get("OOT", "/opt/claude-content-skills/skills")
BASE = pathlib.Path("/opt/viral"); DATA, STATE = BASE/"data", BASE/"state"
OLLAMA, MODEL = "http://localhost:11434/api/generate", "llama3.1:8b"
from google.auth.transport.requests import Request
creds = Credentials.from_authorized_user_file(str(STATE/"token.json"))
if not creds.valid and creds.refresh_token:
    creds.refresh(Request()); (STATE/"token.json").write_text(creds.to_json())
ya = build("youtubeAnalytics", "v2", credentials=creds)
yt = build("youtube", "v3", credentials=creds)
end = datetime.date.today(); start = end - datetime.timedelta(days=30)

def llm(skill_path, prompt):
    return requests.post(OLLAMA, json={"model": MODEL, "stream": False, "system": open(skill_path).read(),
                         "prompt": prompt, "options": {"num_ctx": 8192}}, timeout=600).json()["response"]

jobs = [json.load(open(f)) for f in sorted(glob.glob(str(DATA/"job_*.json")))[-30:]]
jobs = [j for j in jobs if j.get("video_id")]

# 1) /yt-retention — izleyici nerede çıkıyor
retention = []
for j in jobs[-14:]:
    r = ya.reports().query(ids="channel==MINE", startDate=str(start), endDate=str(end),
        metrics="audienceWatchRatio", dimensions="elapsedVideoTimeRatio",
        filters=f"video=={j['video_id']}").execute()
    rows = r.get("rows") or []
    if len(rows) < 10: continue
    p = DATA/f"ret_{j['video_id']}.csv"
    p.write_text("\n".join(f"{x*100:.0f},{y*100:.1f}" for x, y in rows))
    out = subprocess.run(["python3", f"{YTS}/yt-retention/retention.py", str(p), "--json"],
                         capture_output=True, text=True).stdout
    retention.append({"title": j["package"]["title"], "hook": j["hook"]["hook"], "report": out})

# 2) content-audit — kendi medyanına göre multiple
ids = [j["video_id"] for j in jobs]
stats = {}
for k in range(0, len(ids), 50):
    for it in yt.videos().list(part="statistics", id=",".join(ids[k:k+50])).execute().get("items", []):
        stats[it["id"]] = {m: int(v) for m, v in it["statistics"].items() if v.isdigit()}
views = [stats.get(i, {}).get("viewCount", 0) for i in ids]
med = statistics.median(views) if views else 0
audit_rows = [{"title": j["package"]["title"], "goal": j["idea"]["goal"], "formula": j["hook"]["formula"],
               "hook_score": j["hook"]["verdict"], **stats.get(j["video_id"], {}),
               "multiple": round(stats.get(j["video_id"], {}).get("viewCount", 0) / med, 2) if med else 0}
              for j in jobs]

# 3) comment-mining — kendi yorumların (yt-dlp, public)
comments = []
for j in jobs[-10:]:
    try:
        info = subprocess.run(["yt-dlp", "--write-comments", "--skip-download", "--dump-json",
                               "--extractor-args", "youtube:max_comments=30",
                               f"https://www.youtube.com/shorts/{j['video_id']}"],
                              capture_output=True, text=True).stdout
        comments += [c["text"] for c in json.loads(info).get("comments", [])]
    except Exception:
        pass

# 4) trend-spotter — son 7 günün outlier dosyaları
recent = []
for f in sorted(glob.glob(str(DATA/"outliers_*.json")))[-7:]:
    recent += json.load(open(f))["outliers"][:10]

lessons = [
    "## Retention\n" + llm(f"{YTS}/yt-retention/SKILL.md",
        f"{json.dumps(retention, ensure_ascii=False)}\nMax 5 bullets: which hook formulas held, where viewers left, what to change."),
    "## Audit (STOP / KEEP / TEST)\n" + llm(f"{OOT}/content-audit/SKILL.md",
        f"Median views: {med}. Posts: {json.dumps(audit_rows, ensure_ascii=False)}\nGive STOP/KEEP/TEST lists only, each item justified by a multiple."),
    "## Trends (TAKE / ADAPT / SIT OUT)\n" + llm(f"{OOT}/trend-spotter/SKILL.md",
        f"Niche: finance shorts. Last 7 days outliers: {json.dumps(recent, ensure_ascii=False)}\nOnly name trends with real examples above."),
    "## Audience asks\n" + llm(f"{OOT}/comment-mining/SKILL.md",
        f"Comments: {json.dumps(comments[:150], ensure_ascii=False)}\nTop 5 recurring questions with counts + verbatim phrases.") if comments else "",
]
(STATE/"lessons.md").write_text(f"# Lessons ({end})\n\n" + "\n\n".join(x for x in lessons if x))
```

**Slot saatleri** (`best-time-scheduler` mantığı): İlk 4 hafta `SLOTS` sabit kalır ve bu bir **hipotezdir**. 4 hafta sonra Analytics API'den `dimensions=day,insightTrafficSourceType` ile kendi verini çekip saatleri güncelle. Skill'in kuralı gereği veri gelmeden saat değiştirilmez.

---

## 7. n8n zamanlama

| Node | Cron (İstanbul) | Komut |
|---|---|---|
| Daily Viral | `0 6 * * *` | `cd /opt/viral && python3 daily_viral.py --videos 2` |
| Weekly Review | `0 22 * * 0` | `python3 /opt/viral/weekly_review.py` |
| Repo + yt-dlp güncelle | `0 5 * * 1` | `cd /opt/youtube-agent-skill && git pull; cd /opt/claude-content-skills && git pull; pip install -U yt-dlp --break-system-packages` |
| Hata yakalama | Error Trigger → Telegram | stderr'i gönder |

Mevcut 4 formatlı finans pipeline'ının (08:00 recap / 14:00 günün yıldızı / RSS breaking / 22:00 eğitim) yanına **5. format** olarak eklenir: *"Viral formül"*. En ucuz kazanç: Mevcut formatların hook ve başlık adımlarına da `hookscore.py` ve `title.py` kapılarını, ekran yazısına da mute kapısını takmak.

---

## 8. Sınırlar: önceden bil, sürpriz olmasın

1. **Doğrulanmamış API projesi = videolar gizli (private) kalır.** Google, denetimden (audit) geçmemiş OAuth projelerinden yüklenen videoları gizli tutar. Tam otomatik herkese açık yayın için **YouTube API Services audit** başvurusu şart (bir kez yapılır, birkaç hafta sürebilir). O zamana kadar sistem yine tam otomatik üretir ve yükler, videolar sadece gizli kalır. Onay geldikten sonra yüklenen videolar zamanı gelince kendiliğinden yayına girer. Onaydan önce yüklenip kilitlenenler gizli kalabilir.
2. **Kota:** Varsayılan 10.000 birim/gün, `videos.insert` yaklaşık 1.600 birim harcar. Yani günde en fazla ~6 yükleme. Mevcut 4 video + bu 2 video sınırda; gerekirse kota artışı iste.
3. **Sadece YouTube:** Bu sürüm TikTok/IG'ye hiçbir şey göndermez. Genişletme planı §10'da.
4. **"Viral" garanti değil.** `hookscore.py` kendi dokümanında kötü hook'u iyiden iyi ayırdığını, ama bir kanalın hit'ini miss'inden "neredeyse hiç" ayıramadığını söylüyor. Ootto'nun "160+ viral reel" analizi de bir yöntem, garanti değil. Kapılar **kötüyü eler**; asıl sinyal haftalık review döngüsü.
5. **Kopya değil, formül.** İki repo da aynı şeyi söylüyor: yapıyı modelle, kelimeleri asla kopyalama. Prompt'lar birebir hook ve başlık kopyalamayı yasaklıyor. Kopyalar YouTube'un "reused content" politikasına takılır ve erişimi düşürülür.
6. **Scraping kuralları:** yt-dlp ve Reddit JSON sadece public veriyi okur; giriş yapılmaz, çerez kullanılmaz. Reddit 429 verirse o gün talep adımı atlanır, pipeline devam eder. Ootto'nun `agent-reach` aracının tam kurulumu (Exa, Twitter vb.) opsiyoneldir.
7. **Llama 3.1 8B sınırı:** Birkaç SKILL.md'yi birlikte sistem mesajına koyunca bağlam büyür (`num_ctx 8192` ayarlı). JSON bozulursa o slot atlanır ve Telegram'a düşer. Kalite yetmezse **sadece hook + script adımında** daha büyük bir model kullan (Claude API ya da `claude -p` headless). Maliyet günde birkaç bin token'la sınırlı kalır.
8. **Yatırım içeriği uyumu:** Her videoda "Yatırım Tavsiyesi Değildir" var. `going-viral`'daki "öfke/hayret" açıları finans nişinde yanıltıcı iddiaya kaymamalı; voice.md'deki "What I will not claim" bunu sınırlar.

---

## 9. İlk gün kontrol listesi

- [ ] İki repo klonlandı, `$YTS` ve `$OOT` ayarlı
- [ ] `state/voice.md` dolduruldu
- [ ] `state/channels.txt`: en az 10 rakip kanal (her birinden ≥4 video)
- [ ] `state/subreddits.txt`: 3-6 subreddit
- [ ] `state/client_secret.json` + ilk OAuth onayı → `token.json` (scope: youtube.upload, youtube.readonly, yt-analytics.readonly)
- [ ] `market_snapshot.py` mevcut yfinance script'inden JSON döndürüyor
- [ ] Remotion `FinanceShort` composition'ı props'tan `script.beats[].say / osd / emphasis / visual` okuyor
- [ ] `python3 daily_viral.py --videos 1` elle bir kez çalıştırıldı, Telegram raporu geldi
- [ ] OAuth consent screen **"In production"** (yoksa token 7 günde düşer)
- [ ] Remotion'da güvenli format için `DailyRecap` composition'ı var (mevcut recap template'in)
- [ ] YouTube API audit başvurusu yapıldı
- [ ] n8n cron'ları aktif

---

## 10. Sonraki aşama: TikTok + IG Reels (şimdilik kapalı)

Pipeline hazır olduğunda şu 3 adım eklenir, geri kalan her şey aynı kalır:

1. `seo()` fonksiyonunun JSON şemasına `tiktok` ve `instagram` alanları eklenir; sistem mesajına `caption-and-hashtags` ve `cross-platform-reformatter` (Ootto) SKILL.md'leri girer.
2. Yüklemeden sonra bir `distribute_others()` adımı aynı mp4'ü ve platform metinlerini n8n webhook'una gönderir.
3. TikTok Content Posting API ve IG Graph API uygulama onayları alınır. Onay gelene kadar bu platformlar taslak olarak kalır.

# YouTube API audit formu: hazır cevaplar

**Neden şart:** Denetimden geçmemiş bir Google Cloud projesinden `videos.insert` ile yüklenen her video YouTube tarafından **kalıcı olarak gizli (private) kilitlenir**. Onay gelmeden yüklenen videolar sonradan açılamaz. Onaydan sonra yüklenenler normal çalışır.

**Form:** https://support.google.com/youtube/contact/yt_api_form
Açılan sayfada "YouTube API Services - Audit and Quota Extension Form" seçeneğini seç. Formu, Why Stocks Moved kanalının bağlı olduğu Gmail ile doldur.

Aşağıdaki cevapları kopyala-yapıştır. Köşeli parantezleri kendi bilginle doldur.

---

**Google Cloud project number / ID:** `viral-509508`. Proje numarası için: Cloud Console → proje ayarları → "Project number".

**Organization / Company name:** [Adın Soyadın] (individual creator)

**Contact email:** [yeni Gmail adresin]

**Channel(s) the API client will access:** Why Stocks Moved — https://www.youtube.com/@whystocksmoved (channel ID `UCmHXdHe-QmiI9YsioLA9CLQ`)

**Is the API client used only by you / your organization?** Yes. Internal use only, it only accesses my own channel. There are no third-party users.

**Describe your API client / use case:**

```
A private, internal publishing tool for my own YouTube channel "Why Stocks Moved"
(@whystocksmoved). Once a day it builds one or two short vertical educational videos (under
60 seconds) about a real stock-market move of the day, using public end-of-day market data.
It then uploads them to my own channel with a scheduled publish time, adds them to my own
playlists, and once a week reads my own channel's analytics to improve future videos.

The tool is not offered to other users. It runs only for my channel with my own OAuth
credentials, stored as encrypted CI secrets. Every video carries a "Not financial advice"
notice and is declared as containing synthetic media (AI voice-over).
```

**Which API services/methods do you use?**

```
YouTube Data API v3:
 - videos.insert (upload my own Shorts, scheduled publish via status.publishAt)
 - playlistItems.insert, playlists.list/insert (organize my own videos)
 - channels.list/update, channelBanners.insert, watermarks.set (my own channel branding)
 - channels.list, playlistItems.list, videos.list (public stats of competitor channels'
   public Shorts, read-only, to learn which formats perform; ~60 units/day)
 - commentThreads.list (read comments on my own videos, weekly)
YouTube Analytics API:
 - reports.query (my own channel's audience retention, weekly)
```

**Expected daily quota usage:** About 3,500 units/day (2 uploads × 1,600 + ~300 read calls). The default 10,000 quota is enough, no extension requested.

**Do you store YouTube API data? How long?** Only my own videos' IDs, titles and aggregate stats, used for my weekly performance review. Public competitor video titles and view counts are kept up to 30 days to find trends, then discarded. No personal data of other users is stored.

**Do you display YouTube data to other users?** No.

**Screencast / screenshots:** If the form asks for them, send a short screen recording showing the tool running (for example a GitHub Actions log of `daily_viral.py`) and the resulting video in YouTube Studio.

---

Onay genelde birkaç gün ile birkaç hafta arası sürer. E-postayla ek soru gelebilir; gelirse metni bana at, cevabı birlikte yazalım.

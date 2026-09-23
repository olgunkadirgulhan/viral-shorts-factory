# Why Stocks Moved: kanal kurulum paketi

Görseller bu klasörde. Yeniden üretmek için: `python brand/make_brand.py` (isim, slogan veya saat değişirse).

| Dosya | Nereye | Not |
|---|---|---|
| `banner_2560x1440.png` | Studio → Özelleştirme → Marka → **Banner resmi** | Telefonda sadece ortadaki kutu görünür, tüm yazı onun içinde |
| `profile_800x800.png` | Studio → Özelleştirme → Marka → **Resim** | Daire olarak kırpılır, köşeler boş bırakıldı |
| `watermark_150x150.png` | Studio → Özelleştirme → Marka → **Video filigranı** | Opsiyonel. Shorts'ta görünmez, ileride uzun video yaparsan kullanılır |

---

## Temel bilgiler (Studio → Özelleştirme → Temel bilgiler)

**Ad:** `Why Stocks Moved`

**Handle:** `@whystocksmoved`

**Açıklama** (kopyala-yapıştır):

```
Every day, one real market move explained in under 40 seconds.

Why did Nvidia jump? Why is oil falling? What does the Fed decision mean for your portfolio? Each Short takes one move from today's market data, shows you the chart, and explains the cause in plain English: stocks, big tech, earnings, rates, inflation, gold, oil and the dollar.

Real numbers only. No hype, no price predictions, no "buy now".

New Shorts every day at 12:30 PM and 7 PM ET.

Not financial advice. Market data may be delayed. Everything here is for education and information only. Do your own research before making any investment decision.
```

**Bağlantılar:** Şimdilik boş bırak. Gelişmiş özellikler açılmadan açıklama linkleri çalışmaz, zaten gerek yok.

**İletişim e-postası:** Kanal için ayrı bir adres kullan (ör. whystocksmoved.contact@gmail.com). Sponsor ve iş teklifleri buraya gelir.

---

## Ayarlar (Studio → Ayarlar)

**Kanal → Temel bilgiler**
- **Yaşadığın ülke:** Gerçekten yaşadığın ülke. Gelir ve vergi buna göre işler, ABD seçme.
- **Anahtar kelimeler:**
  ```
  why stocks moved, stock market today, stock market news, stocks explained, why is the stock market down, why is the stock market up, nvidia stock, tesla stock, apple stock, big tech stocks, fed rate decision, inflation explained, gold price, oil price, s&p 500, nasdaq, investing for beginners, personal finance, market recap, stock market shorts
  ```

**Kanal → Gelişmiş ayarlar**
- **Kitle:** "Hayır, bu kanal çocuklara özel değil". Pipeline her videoda da bunu gönderiyor.

**Yükleme varsayılanları**
- Dokunmana gerek yok. Pipeline başlık, açıklama, etiket, kategori, dil ve "sentetik içerik" beyanını her videoda API'den gönderiyor.

**Topluluk → Otomatik filtreler** (finans kanalları dolandırıcı yorumlara çok maruz kalır)
- **Bağlantılar:** "Bağlantı içeren yorumları incelemeye tut" → AÇIK
- **Engellenen kelimeler:**
  ```
  whatsapp, telegram, wa.me, t.me, signal app, contact me, text me, dm me, account manager, investment manager, trading expert, broker, forex, binary, recovery, guaranteed profit, 10x, double your, mrs, mr., +1 (, @gmail
  ```
  Bunlar "Mrs. X ile yatırım yaptım, WhatsApp'tan yaz" tipi yorum dolandırıcılığının kalıpları. Kanalın güvenilirliğini ve YouTube'un spam puanını korur.

---

## İlk gün kontrol listesi

- [ ] Banner, profil resmi, ad, handle ve açıklama yüklendi
- [ ] Kitle: çocuklara özel değil
- [ ] Anahtar kelimeler ve yorum filtresi girildi
- [ ] Google Cloud projesi + `python auth_youtube.py --set-github-secrets` → çıktıda kanal adı "Why Stocks Moved" yazıyor
- [ ] GitHub'a `ANTHROPIC_API_KEY` eklendi
- [ ] `state/channels.txt` dolduruldu (10-20 rakip)
- [ ] Actions → Daily viral short → dry run → videolar izlendi

Banner'daki "12:30 PM & 7 PM ET" pipeline'ın `SLOTS` ayarıyla aynı. Yayın saatini değiştirirsen `brand/make_brand.py` içindeki `SCHEDULE` satırını da güncelleyip görselleri yeniden üret.

"""scoring.py — youtube-agent-skill'in hookscore.py ve title.py kapıları, içerik diline göre.

Algoritmalar repodaki dosyalardan birebir yüklenir (ağırlıklar, bantlar, eşikler aynı). Orijinal
sözlükler İngilizce regex'ler olduğu için Türkçe bir hook ADDRESS/STAKES/CURIOSITY'den neredeyse
hiç puan alamaz (~38 civarı, kapı 60). CONTENT_LANG=tr iken sadece kelime listeleri Türkçe
karşılıklarıyla değiştirilir; puanlama mantığına dokunulmaz.
"""
import importlib.util, re

from common import CONTENT_LANG, YTS


def _load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


hs = _load("hookscore", YTS / "yt-script" / "hookscore.py")
tl = _load("title", YTS / "yt-package" / "title.py")


def _tr_lower(t):
    return t.replace("I", "ı").replace("İ", "i").lower()


if CONTENT_LANG == "tr":
    _words = lambda t: re.findall(r"[\w'%$₺.]+", _tr_lower(t))
    hs.words = _words
    hs.FILLER = {"yani", "aslında", "sadece", "gerçekten", "resmen", "şey", "falan", "işte", "arkadaşlar",
                 "merhaba", "selam", "bugün", "video", "videoda", "abone", "kanal", "kanala", "hoşgeldiniz"}
    hs.VAGUE = {"inanılmaz", "müthiş", "harika", "çılgın", "çılgınca", "devasa", "efsane", "efsanevi",
                "muhteşem", "şok", "şoke", "süper", "mükemmel", "akılalmaz", "olağanüstü", "devrim",
                "devrimsel", "gizemli", "büyük"}
    hs.CONCRETE = re.compile(
        r"(\d[\d.,]*\s?(%|k|m|x|bin|milyon|milyar|tl|₺|\$|dolar|lira)?|[%$₺]\s?\d"
        r"|\d+\s?(saniye|dakika|saat|gün|hafta|ay|yıl))", re.I)
    hs.YOU = re.compile(
        r"\b(sen|senin|sana|seni|sende|senden|siz|sizin|size|sizi|sizde|kendin\w*"
        r"|\w+(sın|sin|sun|sün|sınız|siniz|sunuz|sünüz|san|sen|sanız|seniz))\b", re.I)
    hs.STAKE = re.compile(
        r"\b(kaybet\w*|kaybed\w*|kayıp\w*|zarar\w*|batır\w*|bat(tı|ar|ıyor|ma)\w*|boşa|risk\w*|önce"
        r"|dur|durdur\w*|asla|sakın|maliyet\w*|kaçır\w*|eri(yor|di|mesi)\w*|iflas\w*|fakir\w*|pahalı\w*)\b", re.I)
    hs.CURIOSITY = re.compile(
        r"\b(neden|niye|nasıl|ne|hangi|kadar|ama|fakat|kimse|neredeyse|hariç|sebeb\w*|sebep\w*|meğer"
        r"|bilmediğin\w*|gerçek|m[ıiuü])\b", re.I)
    _CLOSED = re.compile(r"\b(çünkü|bu yüzden|bu sayede|yani)\b", re.I)

    def _curiosity(t):
        n = len(hs.CURIOSITY.findall(t))
        q = 18 if t.strip().endswith("?") else 0
        closed = -18 if _CLOSED.search(t) else 0
        return max(0, min(100, 24 + n * 17 + q + closed))

    hs.curiosity = _curiosity
    hs.PROPS = [(n, _curiosity if n == "CURIOSITY" else fn) for n, fn in hs.PROPS]

    tl.words = lambda t: re.findall(r"[\w']+", _tr_lower(t))
    tl.VAGUE = hs.VAGUE | {"tam", "her şey", "kusursuz"}
    tl.STOP = {"ve", "ile", "bir", "bu", "şu", "o", "için", "de", "da", "ki", "mi", "mı", "mu", "mü",
               "ne", "nasıl", "neden", "en", "çok", "sen", "senin", "ben", "benim", "gibi", "daha"}


def score_hooks(texts):
    """hookscore.py --json ile aynı çıktı: verdict'e göre sıralı liste."""
    out = []
    for t in texts:
        parts, verdict, name, _ = hs.score(t)
        out.append({"hook": t.strip(), "properties": parts, "verdict": verdict,
                    "band": hs.band(verdict), "formula": name})
    return sorted(out, key=lambda r: -r["verdict"])


def check_title(title, thumb=None):
    """title.py --title ... --thumb ... --json ile aynı çıktı."""
    return tl.check(title, thumb)


if __name__ == "__main__":
    import json, sys
    for h in score_hooks(sys.argv[1:] or ["Bitcoin 5 günde %12 düştü, sen hâlâ neden bekliyorsun?"]):
        print(json.dumps(h, ensure_ascii=False))

#!/usr/bin/env python3
"""llm_probe.py — LLM servis zincirindeki her servisi ayrı ayrı test eder (anahtar var mı, yanıt geliyor mu).
GitHub'da: Actions → "LLM health check" → Run workflow.   Yerelde: python tools/llm_probe.py
"""
import os, pathlib, sys, time

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))
import common  # noqa: E402

SYSTEM = "You write short, factual stock-market hooks. Reply with JSON only."
PROMPT = 'Return {"hook": "<one 12-word hook about Nvidia moving 2.3% today, addressing the viewer as you>"}'


def gemini_models():
    """Anahtarın erişebildiği, metin üretebilen Gemini modelleri (ad değişikliklerini görmek için)."""
    import requests
    r = requests.get("https://generativelanguage.googleapis.com/v1beta/models",
                     params={"key": os.environ["GEMINI_API_KEY"], "pageSize": 200}, timeout=30)
    if not r.ok:
        print(f"model listesi alınamadı: {r.status_code} {r.text[:200]}")
        return []
    names = [m["name"].split("/")[-1] for m in r.json().get("models", [])
             if "generateContent" in m.get("supportedGenerationMethods", [])]
    print("Gemini erişilebilir modeller:", ", ".join(names))
    return names


def main():
    ok = False
    if os.environ.get("GEMINI_API_KEY"):
        gemini_models()
        import requests
        for m in common.GEMINI_MODELS:
            t0 = time.time()
            try:
                r = common.gemini_request(m, SYSTEM, PROMPT, True)
                msg = r.json().get("error", {}).get("message", "")[:150] if not r.ok else \
                    r.json()["candidates"][0]["content"]["parts"][-1]["text"][:80]
                print(f"  gemini model {m:26} {r.status_code} {time.time() - t0:4.1f}s {msg}")
            except requests.RequestException as e:
                print(f"  gemini model {m:26} {type(e).__name__} {time.time() - t0:4.1f}s")
    for name, (fn, key) in common._BACKENDS.items():
        if name == "ollama":
            continue
        if key and not os.environ.get(key):
            print(f"–    {name:10} anahtar yok ({key})")
            continue
        t0 = time.time()
        try:
            out = common._json_from(fn(SYSTEM, PROMPT, True))
            print(f"OK   {name:10} {time.time() - t0:4.1f}s  {out.get('hook', out)!r}")
            ok = True
        except Exception as e:
            print(f"FAIL {name:10} {str(e)[:220]}")
    print("\nSonuç:", "en az bir servis çalışıyor ✓" if ok else "hiçbir servis çalışmıyor — sistem sadece piyasa özeti yükler")
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()

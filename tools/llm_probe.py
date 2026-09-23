#!/usr/bin/env python3
"""llm_probe.py — LLM servis zincirindeki her servisi ayrı ayrı test eder (anahtar var mı, yanıt geliyor mu).
GitHub'da: Actions → "LLM health check" → Run workflow.   Yerelde: python tools/llm_probe.py
"""
import os, pathlib, sys, time

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))
import common  # noqa: E402

SYSTEM = "You write short, factual stock-market hooks. Reply with JSON only."
PROMPT = 'Return {"hook": "<one 12-word hook about Nvidia moving 2.3% today, addressing the viewer as you>"}'


def main():
    ok = False
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

#!/usr/bin/env python3
"""llm_probe.py — ücretsiz LLM servislerinin bu ortamda çalışıp çalışmadığını ve limitlerini gösterir.
GitHub Actions'ta: "LLM health check" iş akışı (GITHUB_TOKEN ile GitHub Models).
"""
import json, os, sys, time

import requests

GH_URL = "https://models.github.ai/inference/chat/completions"
MODELS = sys.argv[1:] or ["openai/gpt-4.1-mini", "openai/gpt-4o-mini", "openai/gpt-4.1", "openai/gpt-4o",
                          "meta/Llama-3.3-70B-Instruct", "deepseek/DeepSeek-V3-0324", "mistral-ai/mistral-small-2503"]


def main():
    tok = os.environ.get("GITHUB_TOKEN")
    if not tok:
        sys.exit("GITHUB_TOKEN yok")
    H = {"Authorization": f"Bearer {tok}", "Content-Type": "application/json"}
    big = "Market context line. " * 1200          # ~6k token: gerçek prompt boyutu testi
    for m in MODELS:
        for label, content in (("small", "Return {\"ok\": true, \"hook\": \"<10-word stock market hook>\"}"),
                               ("6k", big + "\nReturn {\"ok\": true}")):
            t0 = time.time()
            try:
                r = requests.post(GH_URL, headers=H, timeout=120, json={
                    "model": m, "max_tokens": 200, "response_format": {"type": "json_object"},
                    "messages": [{"role": "system", "content": "Reply with JSON only."},
                                 {"role": "user", "content": content}]})
                rl = {k.lower().replace("x-ratelimit-", ""): v for k, v in r.headers.items() if "ratelimit" in k.lower()}
                if r.ok:
                    out = r.json()["choices"][0]["message"]["content"][:70]
                    print(f"OK   {m:32} {label:5} {time.time() - t0:4.1f}s {out!r} {rl}")
                else:
                    print(f"FAIL {m:32} {label:5} {r.status_code} {r.text[:200]}")
            except Exception as e:
                print(f"ERR  {m:32} {label:5} {str(e)[:150]}")


if __name__ == "__main__":
    main()

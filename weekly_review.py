#!/usr/bin/env python3
"""weekly_review.py — yt-retention + content-audit + trend-spotter + comment-mining → state/lessons.md
Her Pazar çalışır; sonraki haftanın her prompt'u lessons.md'yi okur.
"""
import datetime, glob, json, statistics, sys, traceback

from common import DATA, STATE, PY, YTS, OOT, llm, log, sh, tg, yt_creds, have_yt_creds


def ask(repo_root, name, prompt):
    return llm((repo_root / name / "SKILL.md").read_text(encoding="utf-8"), prompt, as_json=False)


def main():
    from googleapiclient.discovery import build
    if not have_yt_creds():
        log("weekly: YouTube yetkisi yok, atlandı")
        return
    creds = yt_creds()
    ya = build("youtubeAnalytics", "v2", credentials=creds, cache_discovery=False)
    yt = build("youtube", "v3", credentials=creds, cache_discovery=False)
    end = datetime.date.today()
    start = end - datetime.timedelta(days=30)

    jobs = [json.loads(open(f, encoding="utf-8").read()) for f in sorted(glob.glob(str(DATA / "job_*.json")))[-30:]]
    jobs = [j for j in jobs if j.get("video_id") and j["video_id"] != "DRYRUN"]
    if not jobs:
        log("weekly: henüz yayınlanmış video yok, lessons.md değişmedi")
        return

    # 1) /yt-retention — izleyici nerede çıkıyor
    retention = []
    for j in jobs[-14:]:
        try:
            r = ya.reports().query(ids="channel==MINE", startDate=str(start), endDate=str(end),
                                   metrics="audienceWatchRatio", dimensions="elapsedVideoTimeRatio",
                                   filters=f"video=={j['video_id']}").execute()
        except Exception as e:
            log(f"retention atlandı {j['video_id']}: {e}")
            continue
        rows = r.get("rows") or []
        if len(rows) < 10:
            continue
        p = DATA / f"ret_{j['video_id']}.csv"
        p.write_text("\n".join(f"{x * 100:.0f},{y * 100:.1f}" for x, y in rows), encoding="utf-8")
        out = sh([PY, YTS / "yt-retention" / "retention.py", p, "--json"])
        retention.append({"title": j["package"]["title"], "hook": j["hook"]["hook"], "report": out})

    # 2) content-audit — kendi medyanına göre multiple
    ids = [j["video_id"] for j in jobs]
    stats = {}
    for k in range(0, len(ids), 50):
        for it in yt.videos().list(part="statistics", id=",".join(ids[k:k + 50])).execute().get("items", []):
            stats[it["id"]] = {m: int(v) for m, v in it["statistics"].items() if str(v).isdigit()}
    views = [stats.get(i, {}).get("viewCount", 0) for i in ids]
    med = statistics.median(views) if views else 0
    audit_rows = [{"title": j["package"]["title"], "goal": j["idea"]["goal"], "formula": j["hook"]["formula"],
                   "hook_score": j["hook"]["verdict"], **stats.get(j["video_id"], {}),
                   "multiple": round(stats.get(j["video_id"], {}).get("viewCount", 0) / med, 2) if med else 0}
                  for j in jobs]

    # 3) comment-mining — kendi yorumların (commentThreads.list, 1 kota birimi / video)
    comments = []
    for j in jobs[-10:]:
        try:
            r = yt.commentThreads().list(part="snippet", videoId=j["video_id"], maxResults=30,
                                         order="relevance", textFormat="plainText").execute()
            comments += [c["snippet"]["topLevelComment"]["snippet"]["textDisplay"] for c in r.get("items", [])]
        except Exception:
            pass                                                # yorumlar kapalı / video gizli

    # 4) trend-spotter — son 7 günün outlier dosyaları
    recent = []
    for f in sorted(glob.glob(str(DATA / "outliers_*.json")))[-7:]:
        recent += json.loads(open(f, encoding="utf-8").read())["outliers"][:10]

    lessons = [
        "## Retention\n" + (ask(YTS, "yt-retention",
            f"{json.dumps(retention, ensure_ascii=False)}\nMax 5 bullets: which hook formulas held, where viewers left, what to change.")
            if retention else "(yeterli retention verisi yok)"),
        "## Audit (STOP / KEEP / TEST)\n" + ask(OOT, "content-audit",
            f"Median views: {med}. Posts: {json.dumps(audit_rows, ensure_ascii=False)}\nGive STOP/KEEP/TEST lists only, each item justified by a multiple."),
        "## Trends (TAKE / ADAPT / SIT OUT)\n" + ask(OOT, "trend-spotter",
            f"Niche: finance shorts. Last 7 days outliers: {json.dumps(recent, ensure_ascii=False)}\nOnly name trends with real examples above.")
            if recent else "",
        "## Audience asks\n" + ask(OOT, "comment-mining",
            f"Comments: {json.dumps(comments[:150], ensure_ascii=False)}\nTop 5 recurring questions with counts + verbatim phrases.")
            if comments else "",
    ]
    (STATE / "lessons.md").write_text(f"# Lessons ({end})\n\n" + "\n\n".join(x for x in lessons if x), encoding="utf-8")
    log(f"weekly: lessons.md güncellendi ({len(jobs)} video, {len(retention)} retention, {len(comments)} yorum)")
    tg(f"📊 Haftalık review tamam: {len(jobs)} video, medyan {med:.0f} izlenme. lessons.md güncellendi.")


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        log(traceback.format_exc())
        tg(f"❌ weekly_review çöktü: {str(e)[:500]}")
        sys.exit(1)

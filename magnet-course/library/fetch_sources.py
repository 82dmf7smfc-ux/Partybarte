"""Fetch every source in sources.json, cache it, and log the result.

Run this on the first session that has network access:

    python3 magnet-course/library/fetch_sources.py

It walks library/sources.json, requests each URL, saves free sources into
library/pdf/, appends a dated block per source to library/verified.log, and
writes the real HTTP status back into the verification object in sources.json.

Standard library only. It runs before magpylib or anything else is installed,
and it has to work on a machine where pip may still be blocked.

Options:

    --only KEY[,KEY...]   fetch just these keys
    --retry               re-fetch sources that already succeeded
    --include-paid        also request the paywalled entries, to record what
                          the paywall actually returns. Off by default, since
                          those four are not meant to be bought.
    --timeout SECONDS     per request, default 60
    --dry-run             list what would be fetched, touch nothing

What it deliberately does not do. It never writes the contents line. That line
says what the document actually holds, which is often not what its title
suggests, and only reading it can answer that. The log gets "contents: PENDING,
fetched but not yet read" and stays that way until a person or a model reads
the file and fills it in. A fetch is not verification.
"""

import argparse
import json
import sys
import urllib.error
import urllib.request
from datetime import date, datetime, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
SOURCES = HERE / "sources.json"
LOG = HERE / "verified.log"
PDF = HERE / "pdf"

# Some hosts refuse the default urllib agent. Identify honestly instead.
UA = ("magnet-course-library/1.0 (source cache for a private study course; "
      "one request per source)")

EXT_BY_TYPE = {
    "application/pdf": ".pdf",
    "text/html": ".html",
    "application/xhtml+xml": ".html",
    "text/plain": ".txt",
}

RULE = "-" * 80


def classify(status, content_type, free):
    """Turn an outcome into one of the vocabulary words used in verified.log."""
    if status is None:
        return "unreachable"
    if status == 200:
        if not free:
            return "paywalled"
        if content_type.startswith("text/html"):
            # A landing page is a real result, but it is not the document.
            return "ok_landing_page"
        return "ok"
    if status in (401, 402, 403):
        return "paywalled" if not free else "forbidden"
    if status == 404:
        return "dead"
    return "error"


def fetch(url, timeout):
    """Return (status, content_type, body, final_url, error). Never raises."""
    req = urllib.request.Request(url, headers={
        "User-Agent": UA,
        "Accept": "*/*",
    })
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            body = r.read()
            ctype = (r.headers.get("Content-Type") or "").split(";")[0].strip().lower()
            return r.status, ctype, body, r.url, None
    except urllib.error.HTTPError as e:
        # An HTTP error is still an answer from the server. Record it.
        ctype = (e.headers.get("Content-Type") or "").split(";")[0].strip().lower() if e.headers else ""
        return e.code, ctype, None, url, "HTTP %s %s" % (e.code, e.reason)
    except urllib.error.URLError as e:
        return None, "", None, url, "transport error: %s" % (e.reason,)
    except Exception as e:  # socket timeouts, malformed responses, bad TLS
        return None, "", None, url, "%s: %s" % (type(e).__name__, e)


def cache_name(key, ctype, url):
    ext = EXT_BY_TYPE.get(ctype)
    if ext is None:
        tail = url.rsplit("/", 1)[-1]
        ext = "." + tail.rsplit(".", 1)[-1] if "." in tail and len(tail.rsplit(".", 1)[-1]) <= 5 else ".bin"
    return key + ext


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--only", default="")
    ap.add_argument("--retry", action="store_true")
    ap.add_argument("--include-paid", action="store_true")
    ap.add_argument("--timeout", type=float, default=60.0)
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args(argv)

    doc = json.loads(SOURCES.read_text(encoding="utf-8"))
    sources = doc["sources"]

    wanted = [k.strip() for k in args.only.split(",") if k.strip()] or list(sources)
    unknown = [k for k in wanted if k not in sources]
    if unknown:
        sys.exit("No such key in sources.json: " + ", ".join(unknown))

    todo = []
    for key in wanted:
        s = sources[key]
        if not s["free"] and not args.include_paid:
            continue
        if s["verification"]["fetched"] and not args.retry:
            continue
        todo.append(key)

    if not todo:
        print("Nothing to do. Everything requested is already fetched. "
              "Use --retry to force.")
        return 0

    print("%d source%s to fetch." % (len(todo), "" if len(todo) == 1 else "s"))
    if args.dry_run:
        for key in todo:
            print("  %-12s %s" % (key, sources[key]["url"]))
        return 0

    PDF.mkdir(parents=True, exist_ok=True)
    today = date.today().isoformat()
    stamp = datetime.now(timezone.utc).isoformat(timespec="seconds")

    blocks = []
    tally = {}
    for i, key in enumerate(todo, 1):
        s = sources[key]
        url = s["url"]
        print("[%2d/%2d] %-12s %s" % (i, len(todo), key, url), flush=True)

        status, ctype, body, final_url, err = fetch(url, args.timeout)
        result = classify(status, ctype, s["free"])
        tally[result] = tally.get(result, 0) + 1

        cached = None
        if body:
            cached = cache_name(key, ctype, final_url)
            (PDF / cached).write_bytes(body)

        v = s["verification"]
        v.update({
            "fetched": body is not None,
            "date": today,
            "http_status": status,
            "content_type": ctype or None,
            "bytes": len(body) if body else None,
            "cached_as": cached,
            "result": result,
        })
        if final_url != url:
            v["redirected_to"] = final_url
        if err:
            v["error"] = err
        # contents is left exactly as it was. Only reading the document
        # justifies writing it, and this script has not read anything.

        blocks.append(
            "key:      %s\n"
            "url:      %s\n"
            "date:     %s\n"
            "result:   %s\n"
            "status:   %s\n"
            "cached:   %s\n"
            "contents: %s\n"
            % (
                key,
                url + ("" if final_url == url else "\n          redirected to " + final_url),
                today,
                result,
                err or ("HTTP %s, %s, %d bytes" % (status, ctype or "no content type", len(body or b""))),
                cached or "none",
                v["contents"] or (
                    "PENDING, fetched but not yet read."
                    if body else "unknown. Nothing was retrieved, so nothing was read."
                ),
            )
        )

    doc["sources"] = sources
    SOURCES.write_text(json.dumps(doc, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    header = (
        "\n" + "=" * 80 + "\n"
        "FETCH PASS, %s\n" % stamp +
        "=" * 80 + "\n\n"
        "%d source%s requested. Outcomes: %s\n\n"
        % (
            len(todo), "" if len(todo) == 1 else "s",
            ", ".join("%s %d" % (k, n) for k, n in sorted(tally.items())) or "none",
        )
    )
    with LOG.open("a", encoding="utf-8") as f:
        f.write(header + ("\n" + RULE + "\n\n").join(blocks) + "\n")

    print("\nOutcomes: " + ", ".join("%s %d" % (k, n) for k, n in sorted(tally.items())))
    print("Appended %d blocks to %s" % (len(blocks), LOG))
    print("Cached files are in %s" % PDF)
    print("\nNext: read what landed and write the contents line for each, in "
          "sources.json and in the log. Nothing may be cited until then.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

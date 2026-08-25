"""Build library/sources.json from the S object in the syllabus HTML.

The syllabus is the single source of truth for which documents this course
cites. Retyping that list by hand invites drift, so it is extracted by script
instead. Re-run this any time the syllabus S object changes.

    python3 magnet-course/library/extract_sources.py

What this script does and does not do:

  It copies key, title, url and free straight out of the syllabus, and the
  sub field, which carries the "buy only if" reasoning on paid entries.

  It derives publisher and type from the URL host and path, using the table
  below. Nothing is derived from memory. If a host is not in the table the
  fields come out null rather than guessed.

  It derives year only when a year is literally present in the arXiv
  identifier, the URL path, or the title text, and it records which of those
  it used in year_basis. Anything else is null.

  It does not fetch anything. Every entry it writes is marked unverified.
  Run fetch_sources.py to fill in the verification block.
"""

import json
import re
from datetime import date
from pathlib import Path

HERE = Path(__file__).resolve().parent
SYLLABUS = HERE.parent / "syllabus" / "magnet-bench-syllabus.html"
OUT = HERE / "sources.json"

# Host to publisher and default document type. Derived from the URL alone.
# Anything not listed here comes out null rather than guessed.
HOSTS = {
    "arxiv.org":                    ("arXiv", "preprint"),
    "cds.cern.ch":                  ("CERN Document Server", "proceedings"),
    "cas.web.cern.ch":              ("CERN Accelerator School", "course page"),
    "indico.cern.ch":               ("CERN Indico", "slides"),
    "wpw.bnl.gov":                  ("Brookhaven National Laboratory", "lecture notes"),
    "www.bnl.gov":                  ("Brookhaven National Laboratory", "report"),
    "www.diamond.ac.uk":            ("Diamond Light Source", "slides"),
    "www.esrf.fr":                  ("ESRF", "slides"),
    "uspas.fnal.gov":               ("US Particle Accelerator School", "course page"),
    "www.femm.info":                ("FEMM (David Meeker)", "documentation"),
    "sourceforge.net":              ("SourceForge", "wiki"),
    "magpylib.readthedocs.io":      ("Magpylib project", "documentation"),
    "github.com":                   ("GitHub", "source repository"),
    "www.sciencedirect.com":        ("Elsevier", "journal article"),
    "www.arnoldmagnetics.com":      ("Arnold Magnetic Technologies", "white paper"),
    "www.allegromicro.com":         ("Allegro MicroSystems (Arnold document)", "white paper"),
    "www.automate.org":             ("A3, Association for Advancing Automation", "industry guideline"),
    "www.duramag.com":              ("Dura Magnetics", "vendor download page"),
    "eprintspublications.npl.co.uk": ("National Physical Laboratory", "laboratory report"),
    "www.ama-science.org":          ("AMA Science", "proceedings"),
    "pypi.org":                     ("Python Package Index", "package page"),
    "magnetism.eu":                 ("European Magnetism Association", "index page"),
    "www.nist.gov":                 ("NIST", "web page"),
    "physics.nist.gov":             ("NIST", "bibliography"),
    "nvlpubs.nist.gov":             ("NIST", "technical note"),
    "www.astm.org":                 ("ASTM International", "standard"),
    "webstore.ansi.org":            ("ANSI Webstore, for IEC", "standard"),
    "ieeexplore.ieee.org":          ("IEEE", "journal article"),
    "www.magcam.com":               ("MagCam NV", "vendor article"),
    # DOI prefix 10.3390 is registered to MDPI. That is a registry fact carried
    # in the identifier itself, not a recollection about the paper.
    "doi.org":                      (None, "journal article"),
}

DOI_PREFIX = {"10.3390": "MDPI"}

ENTRY = re.compile(
    r'^\s*(?P<key>\w+)\s*:\s*\{'
    r'\s*t\s*:\s*"(?P<t>[^"]*)"'
    r'\s*,\s*u\s*:\s*"(?P<u>[^"]*)"'
    r'\s*,\s*f\s*:\s*(?P<f>[01])'
    r'(?:\s*,\s*sub\s*:\s*"(?P<sub>[^"]*)")?'
    r'\s*\}\s*,?\s*$'
)


def read_s_object(html):
    """Return the raw text of the S object, without its braces."""
    body = html.split("const S={", 1)[1]
    return body.split("\n};", 1)[0]


def host_of(url):
    return url.split("//", 1)[-1].split("/", 1)[0]


def derive_publisher_type(url):
    host = host_of(url)
    publisher, kind = HOSTS.get(host, (None, None))
    if host == "doi.org":
        prefix = url.split("doi.org/", 1)[-1].split("/", 1)[0]
        publisher = DOI_PREFIX.get(prefix)
    if host == "www.femm.info":
        kind = "manual" if url.endswith(".pdf") else "FAQ"
    return host, publisher, kind


# A year must stand on its own. Bounded by non digits on both sides, so that
# the 2030 buried in a ScienceDirect PII like S2352711020300170, or any other
# long identifier, is not read as a date.
YEAR = re.compile(r"(?<!\d)(19|20)\d{2}(?!\d)")


def years_in(text):
    """Every standalone four digit year in text, up to the current one."""
    this_year = date.today().year
    out = []
    for m in YEAR.finditer(text):
        y = int(m.group(0))
        if 1900 <= y <= this_year and y not in out:
            out.append(y)
    return out


def derive_year(url, title):
    """Year, plus a one line record of where it came from. Never a guess."""
    m = re.search(r"arxiv\.org/(?:abs|pdf)/(\d{2})(\d{2})\.", url)
    if m:
        yy, mm = m.group(1), m.group(2)
        year = 2000 + int(yy)
        return year, ("arXiv identifier %s%s, which encodes the posting month "
                      "%04d-%s. This is when the preprint went up, which for a "
                      "lecture note can be later than the lecture itself."
                      % (yy, mm, year, mm))

    found = years_in(title)
    if found:
        basis = "year appears literally in the syllabus title text"
        if len(found) > 1:
            basis += (". The title carries more than one year, %s. The first is "
                      "taken. Confirm on fetch." % ", ".join(str(y) for y in found))
        return found[0], basis

    # Skip the scheme and the host, so a numeric host or port cannot match.
    tail = url.split("//", 1)[-1]
    path = tail[tail.index("/"):] if "/" in tail else ""
    found = years_in(path)
    if found:
        return found[0], ("year appears in the URL path. This can be an upload "
                          "or revision date rather than the publication date. "
                          "Confirm on fetch.")

    return None, "no year is present in the identifier, the title, or the URL"


def main():
    html = SYLLABUS.read_text(encoding="utf-8")
    raw = read_s_object(html)

    sources, keys, skipped = {}, [], []
    today = date.today().isoformat()

    for line in raw.splitlines():
        if not line.strip():
            continue
        m = ENTRY.match(line)
        if not m:
            skipped.append(line.strip())
            continue
        key, url, title = m.group("key"), m.group("u"), m.group("t")
        host, publisher, kind = derive_publisher_type(url)
        year, year_basis = derive_year(url, title)
        keys.append(key)
        sources[key] = {
            "key": key,
            "title": title,
            "url": url,
            "free": m.group("f") == "1",
            "free_alternative_note": m.group("sub"),
            "host": host,
            "publisher": publisher,
            "type": kind,
            "year": year,
            "year_basis": year_basis,
            "verification": {
                "fetched": False,
                "date": today,
                "http_status": None,
                "content_type": None,
                "bytes": None,
                "cached_as": None,
                "result": "egress_denied",
                "contents": None,
                "replaced_by": None,
            },
        }

    if skipped:
        raise SystemExit("Unparsed lines in the S object:\n  " + "\n  ".join(skipped))
    if len(keys) != len(set(keys)):
        raise SystemExit("Duplicate keys in the S object.")

    doc = {
        "_readme": [
            "Source index for the magnet metrology course. Generated by",
            "extract_sources.py from the S object in",
            "syllabus/magnet-bench-syllabus.html. Do not edit key, title, url or",
            "free by hand: change the syllabus and re-run the script.",
            "",
            "publisher and type are derived from the URL host and path only.",
            "year is derived only from a year literally present in the arXiv",
            "identifier, the title, or the URL path, and year_basis says which.",
            "None of it is confirmed against the document. The verification",
            "block is the authority on that, and fetch_sources.py fills it in.",
        ],
        "generated": today,
        "generator": "library/extract_sources.py",
        "source_of_truth": "syllabus/magnet-bench-syllabus.html, const S",
        "count": len(sources),
        "sources": sources,
    }
    OUT.write_text(json.dumps(doc, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print("wrote %s with %d sources" % (OUT, len(sources)))
    print("free: %d, paid: %d" % (
        sum(1 for s in sources.values() if s["free"]),
        sum(1 for s in sources.values() if not s["free"]),
    ))
    unknown = sorted({s["host"] for s in sources.values() if s["publisher"] is None})
    if unknown:
        print("hosts with no publisher mapping: " + ", ".join(unknown))


if __name__ == "__main__":
    main()

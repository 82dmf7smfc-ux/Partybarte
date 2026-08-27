"""Build library/sources.json from the S object in the syllabus HTML.

Only two things are written here: what the syllabus itself says, and what can be
read off the URL string. Publisher comes from the hostname. Year is filled in
only where the identifier encodes it, for example an arXiv number of the form
YYMM.NNNNN. Everything else is left null with a basis of "needs fetch", so that
no field in this file is a guess.

Usage:
    python3 tools/build_sources.py
"""

import json
import re
import subprocess
import sys
from pathlib import Path
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parent.parent
SYLLABUS = ROOT / "syllabus" / "magnet-bench-syllabus.html"
OUT = ROOT / "library" / "sources.json"

# Hostname to publisher. Read off the URL, not from memory.
PUBLISHERS = {
    "arxiv.org": "arXiv",
    "cds.cern.ch": "CERN Document Server",
    "cas.web.cern.ch": "CERN Accelerator School",
    "indico.cern.ch": "CERN Indico",
    "www.bnl.gov": "Brookhaven National Laboratory",
    "wpw.bnl.gov": "Brookhaven National Laboratory",
    "www.diamond.ac.uk": "Diamond Light Source",
    "www.esrf.fr": "ESRF",
    "www.femm.info": "FEMM (David Meeker)",
    "sourceforge.net": "SourceForge",
    "magpylib.readthedocs.io": "Read the Docs",
    "github.com": "GitHub",
    "www.sciencedirect.com": "Elsevier (SoftwareX, open access)",
    "www.arnoldmagnetics.com": "Arnold Magnetic Technologies",
    "www.allegromicro.com": "Allegro MicroSystems (hosting Arnold document)",
    "www.automate.org": "A3 (hosting MMPA document)",
    "www.duramag.com": "Duramag / Bunting",
    "eprintspublications.npl.co.uk": "National Physical Laboratory",
    "www.ama-science.org": "AMA Science",
    "pypi.org": "PyPI",
    "magnetism.eu": "European Magnetism Association",
    "www.nist.gov": "NIST",
    "nvlpubs.nist.gov": "NIST",
    "physics.nist.gov": "NIST",
    "www.astm.org": "ASTM International",
    "webstore.ansi.org": "ANSI Webstore (IEC)",
    "www.magcam.com": "MagCam NV",
    "ieeexplore.ieee.org": "IEEE",
    "doi.org": "DOI resolver",
    "uspas.fnal.gov": "US Particle Accelerator School",
}

# Document type. Read off the title and URL, both local facts.
TYPES = {
    "hall": "lecture notes", "coils": "lecture notes", "bahrdt": "lecture notes",
    "sgobba": "lecture notes", "cas": "proceedings", "casprog": "conference programme",
    "jainov": "lecture slides", "jainus": "lecture archive", "jainharm": "lecture slides",
    "jainaxis": "lecture slides", "immw20": "conference presentation",
    "immw12": "conference presentation", "femmman": "software manual",
    "femmtut": "software tutorial", "femmfaq": "software FAQ",
    "femmcas": "lecture slides", "feexer": "tutorial paper",
    "magpy": "software documentation", "magpygh": "software repository",
    "magpypaper": "journal article", "arnoldmeas": "vendor white paper",
    "arnoldunder": "vendor white paper", "pmg88": "industry guideline",
    "mmpa": "industry standard portal", "npl": "national laboratory report",
    "amamag": "conference proceedings", "radia": "software package",
    "ema": "software index", "tn1297": "standards body landing page",
    "tn1297pdf": "technical note", "nistunc": "topic page",
    "nistbib": "bibliography", "a977": "standard", "a773": "standard",
    "iec": "standard", "magcam": "vendor blog post", "magcamieee": "journal article",
    "bcam": "preprint", "visc": "journal article", "uspas": "course archive",
}


def year_from_url(url):
    """Return (year, basis) where the identifier itself encodes the year."""
    m = re.search(r"arxiv\.org/(?:abs|pdf)/(\d{2})(\d{2})\.\d{4,5}", url)
    if m:
        yy = int(m.group(1))
        return 1900 + yy if yy >= 91 else 2000 + yy, "encoded in the arXiv identifier"
    m = re.search(r"cern-(\d{4})-\d+", url, re.I)
    if m:
        return int(m.group(1)), "encoded in the CERN report number"
    return None, "needs fetch"


def main():
    sys.path.insert(0, str(ROOT / "tools"))
    raw = subprocess.run(
        [sys.executable, str(ROOT / "tools" / "extract_syllabus.py"), str(SYLLABUS)],
        capture_output=True, text=True, check=True,
    ).stdout
    syl = json.loads(raw)

    # Which classes cite each source, so the library records what depends on it.
    cited_by = {}
    for cls in syl["classes"]:
        for s in cls["sources"]:
            cited_by.setdefault(s["key"], []).append(cls["id"])

    sources = {}
    for key, s in syl["sources"].items():
        host = urlparse(s["u"]).netloc
        year, basis = year_from_url(s["u"])
        sources[key] = {
            "key": key,
            "title": s["t"],
            "url": s["u"],
            "free": bool(s["f"]),
            "publisher": PUBLISHERS.get(host, host),
            "type": TYPES.get(key, "unknown"),
            "year": year,
            "year_basis": basis,
            "free_substitute_note": s.get("sub"),
            "cited_by_classes": cited_by.get(key, []),
            "verification": {
                "last_attempt": None,
                "result": "not attempted",
                "detail": None,
                "contains": None,
                "cached_pdf": None,
                "notes_file": None,
            },
        }

    out = {
        "generated_by": "tools/build_sources.py from syllabus/magnet-bench-syllabus.html",
        "source_count": len(sources),
        "free_count": sum(1 for v in sources.values() if v["free"]),
        "paid_count": sum(1 for v in sources.values() if not v["free"]),
        "sources": sources,
    }
    OUT.write_text(json.dumps(out, indent=1) + "\n")
    print("wrote %s with %d sources (%d free, %d paid)"
          % (OUT.relative_to(ROOT), out["source_count"], out["free_count"], out["paid_count"]))


if __name__ == "__main__":
    main()

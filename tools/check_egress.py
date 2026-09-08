"""Report which hosts this machine can actually reach, and what that costs you.

Written because a whole development session on this project ran with PyPI
silently blocked. Every local `pip install` failed with "no matching
distribution", which reads as a bad version pin rather than a firewall, and the
Python test suite could not be run at all. CI was the only verification for two
days before anyone noticed why.

So this asks the question directly, on a new machine, before that happens again.
It reaches nothing sensitive and sends nothing anywhere: it opens a connection
to each host and reports the status code.

    python tools/check_egress.py

Standard library only, so it runs before the virtual environment exists. That is
the point: the thing it is diagnosing is why the environment will not build.
"""

import argparse
import socket
import ssl
import sys
import urllib.error
import urllib.request

TIMEOUT = 12

# What the project needs, and what breaks without it. Grouped so the report can
# say "git works but you cannot install anything", which is the exact state this
# script was written in.
HOSTS = [
    ("github.com", "git", "clone, fetch and push over HTTPS"),
    ("api.github.com", "git", "pull requests, releases and CI status"),
    ("codeload.github.com", "git", "source archive downloads"),
    ("objects.githubusercontent.com", "git", "release asset downloads"),
    ("pypi.org", "pip", "finding packages"),
    ("files.pythonhosted.org", "pip", "downloading the wheels themselves"),
]

GROUP_MEANING = {
    "git": (
        "Version control and CI. Without these you cannot clone, push, or read\n"
        "     CI results. Nothing else in this project works around that."
    ),
    "pip": (
        "Installing Python packages. Without these, build the virtual\n"
        "     environment from a wheel folder instead:\n"
        "       setup_venv.bat C:\\path\\to\\wheels        (Windows)\n"
        "       ./setup_venv.sh /path/to/wheels           (macOS, Linux)\n"
        "     docs/WHEELS.md lists exactly which wheels to ask IT for."
    ),
}


def probe(host):
    """Return (ok, detail) for one host. Never raises."""
    url = "https://%s/" % host
    request = urllib.request.Request(url, method="HEAD", headers={"User-Agent": "alarm-pareto-egress-check"})
    try:
        with urllib.request.urlopen(request, timeout=TIMEOUT) as response:
            return True, "HTTP %d" % response.status
    except urllib.error.HTTPError as err:
        # A 403 or 407 from a proxy is a policy denial, and is the case this
        # script exists to name. A 404 or 405 means the host answered, which is
        # all we are asking: the host is reachable.
        if err.code in (403, 407):
            return False, "HTTP %d, blocked by policy" % err.code
        return True, "HTTP %d, reachable" % err.code
    except urllib.error.URLError as err:
        reason = getattr(err, "reason", err)
        if isinstance(reason, ssl.SSLError):
            return False, "TLS failed: %s" % reason
        if isinstance(reason, socket.timeout):
            return False, "timed out after %ds" % TIMEOUT
        return False, "unreachable: %s" % reason
    except Exception as err:  # noqa: BLE001 - a diagnostic must never crash
        return False, "failed: %s" % err


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--quiet", action="store_true",
        help="print only the summary line and the blocked hosts",
    )
    args = parser.parse_args(argv)

    print("Checking what this machine can reach. Nothing is sent anywhere.\n")

    results = []
    for host, group, why in HOSTS:
        ok, detail = probe(host)
        results.append((host, group, why, ok, detail))
        if not args.quiet or not ok:
            print("  %-4s %-32s %s" % ("ok" if ok else "BLOCK", host, detail))
            if not args.quiet:
                print("       %s" % why)

    print()
    blocked_groups = sorted({g for _, g, _, ok, _ in results if not ok})
    if not blocked_groups:
        print("Everything this project needs is reachable.")
        return 0

    print("Blocked, and what it means:\n")
    for group in blocked_groups:
        names = [h for h, g, _, ok, _ in results if g == group and not ok]
        print("  %s (%s)" % (group, ", ".join(names)))
        print("     %s\n" % GROUP_MEANING[group])

    # A blocked host is a fact about the network, not a fault in this checkout.
    # Exit 0 so a setup script can run this for information without failing.
    print("This is your network's egress policy, not a problem with the repository.")
    print("Ask whoever administers it to allow the hosts above, or work offline")
    print("from a wheel folder as described.")
    return 0


if __name__ == "__main__":
    sys.exit(main())

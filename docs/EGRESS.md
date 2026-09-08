# What the network has to allow

Re-check this on every new machine. `python tools/check_egress.py` asks the
questions in this file automatically and needs no packages, so it runs before the
virtual environment exists.

## Measured, not assumed

These are results from the environment this project was last developed in, which
is a good example of a partially blocked network:

| Host | Result | Consequence |
|---|---|---|
| `github.com` | reachable | clone, fetch, push all work |
| `api.github.com` | reachable | pull requests, releases, CI status all work |
| `codeload.github.com` | reachable | source archives work |
| `objects.githubusercontent.com` | reachable | release assets download |
| `pypi.org` | **HTTP 403** | cannot install any Python package |
| `files.pythonhosted.org` | **HTTP 403** | cannot download any wheel |
| `archive.ubuntu.com` | **denied at CONNECT** | cannot install OS packages either |

What that combination costs: git and CI work perfectly, and the Python test suite
cannot be run locally at all. Every `pip install` fails with "no matching
distribution found", which reads as a bad version pin rather than a firewall.

That is the trap. A session lost two days to it, verifying only through CI and
not realising why the local install kept failing. If `check_egress.py` reports
`pip` blocked, believe it and go straight to the wheel folder route in
`docs/WHEELS.md`.

Note that a host can be on a proxy's direct-connect list and still be blocked:
in that environment `pypi.org` was explicitly listed as no-proxy and returned 403
anyway, because the block was at the network gateway rather than in the proxy's
own allowlist. Being on an allowlist is not evidence of reachability. Probing is.

## What to ask for

**Required, or nothing works:**

- `github.com`, `api.github.com`, `codeload.github.com`,
  `objects.githubusercontent.com` — version control and CI.

**Required unless you work from a wheel folder:**

- `pypi.org`, `files.pythonhosted.org` — installing Python packages.

If PyPI cannot be opened, that is a workable answer, not a blocker. The project
is designed for it: `requirements.txt` is fully pinned, `setup_venv.bat` and
`setup_venv.sh` both take a wheel folder, and `docs/WHEELS.md` says what to put
in it. The offline route is the normal route for a bench machine.

**Not needed at all:**

- Nothing at runtime. Both tools are fully offline by design. The browser tool
  makes no network calls whatever and must keep it that way; that rule is in
  `CLAUDE.md` and it is what lets the page open from a USB stick on a bench
  machine with no network at all.

## If TLS fails rather than the host being blocked

A corporate network that re-terminates TLS needs its certificate authority
trusted, or every HTTPS tool reports a certificate error that looks like a
different problem. Point the tool at the bundle rather than disabling
verification:

```
pip config set global.cert C:\path\to\ca-bundle.crt
git config --global http.sslCAInfo C:\path\to\ca-bundle.crt
```

Never disable certificate verification to get past this. It is the one shortcut
here that trades a working install for a real security problem.

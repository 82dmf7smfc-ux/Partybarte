---
name: cut-a-release
description: Publish a new version of the tools. Use when asked to cut, tag, ship, or publish a release, bump the version, or build the distributable zip packages for the bench.
---

# Cutting a release

Releases are built by GitHub Actions, not by hand. The job runs the tests,
builds both zip packages with `tools/build_zips.py`, and attaches them to a new
GitHub Release. Building the same way every time is the point.

## Before tagging

1. **Everything green on `main`.** Both checks:

       node tools/check_parity.mjs
       python -m pytest -q

2. **The changelog is real.** Move the "Unreleased" items under a new version
   heading with today's date. Write it for someone deciding whether to upgrade,
   not for someone reading the diff. Say plainly if any reported number changed,
   because people have old reports on slides.

3. **Pick the version.** Semantic versioning.
   - Patch, `1.0.1`. A fix that does not change any number a user sees.
   - Minor, `1.1.0`. New capability, old numbers unchanged.
   - Major, `2.0.0`. Any change to what the numbers mean. Changing an analysis
     result is a breaking change here even though nothing about the interface
     moved. People trust these numbers.

4. **Check the browser tool opens.** It is the version most people use. Open
   `alarm_pareto.html`, load the built-in sample, and confirm the charts render.

## Tagging

    git tag v1.2.0
    git push origin v1.2.0

The release workflow can also be run by hand from the Actions tab if a tag
cannot be pushed. It takes the version as an input.

## After

Check that the Release has both zip files attached and that the browser package
contains `alarm_pareto.html` plus `packaging/browser_READ_ME_FIRST.txt`.
Download one and open the HTML file. A release nobody can open is worse than no
release.

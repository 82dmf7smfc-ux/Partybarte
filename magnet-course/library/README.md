# The library

Rules live in `CLAUDE.md`. This file records the decisions made about how the
library is stored.

## Why `library/pdf/` is tracked in git

The cache is in version control. The alternative, ignoring it and relying on the
URLs, loses the archive the first time this repository is cloned to a new
machine or the first time a vendor reorganises a website.

The argument for tracking:

- The point of the cache is durability. `CLAUDE.md` says vendor white papers and
  lab reports disappear without warning. A cache that is not in history does not
  survive a disk change, so it is not an archive, it is a temporary folder.
- These files are written once and never modified. Git's cost problem with
  binary files is repeated modification, because each revision stores a whole
  new copy. A PDF added once and never touched again costs its own size, one
  time. A hundred megabytes of write-once PDFs is a hundred megabytes of history,
  not a growing burden.
- The BibTeX export and the notes are useless without the documents they point
  at. Keeping them in different places guarantees they drift apart.

The argument against, and why it did not win: clone time. A large cache makes a
fresh clone slower. That cost is paid rarely, and it buys an archive that still
resolves in ten years. For a project whose stated purpose is tracking magnets
over years, that trade is obvious.

## When to revisit

Run the size check:

```
du -sh library/pdf/
```

Revisit this decision if the cache passes roughly 250 MB, or if a single source
is larger than about 50 MB. The likely trigger is `cas`, the full CAS Bruges
2009 proceedings, which is a complete volume rather than a single lecture. If
that one file dominates, the first thing to try is caching only the individual
lectures actually cited, `hall`, `coils`, `bahrdt`, and `sgobba`, and keeping a
pointer to the full volume rather than the volume itself.

If the cache does have to leave git, move it to Git LFS rather than to
`.gitignore`. Ignoring it silently converts an archive into a cache, which is
the failure this repository is built to avoid.

## Current state

The cache is empty. No source has been fetched. See `verified.log` for why.

# Decisions log, fab equipment driver library

The running record of choices made and why. Add to it whenever an architecture
decision is made. Date every entry. A decision without its reason is just a rule
someone will break later.

## Why this file is not called CLAUDE.md

The reference CTI project keeps its decisions in `CLAUDE.md`. That filename has a
second meaning: Claude Code reads it automatically as standing instructions for
any session working in that folder. A long decisions log in that file would be
read as a list of orders every time. So the log lives here, and `CLAUDE.md` is
left free for actual working instructions if we ever want them.

## Decisions

- **2026-09-02. The library is one project, not ten.** The prompt describes ten
  drivers and calls each one a project. They are subpackages under
  `fab_drivers/devices/` instead. The reason is the shared service layer: every
  driver is meant to plug into one poller and one trend page. Ten separate
  projects would have to import each other's code, which the repository's
  contributing guide forbids, or copy the same scaffolding ten times.

- **2026-09-02. The core layer was built before any driver.** So the first real
  driver drops into a tested template rather than inventing one and having the
  next nine copy its mistakes.

- **2026-09-02. Read-only is enforced by an allowed list, not by discipline.**
  Every driver declares the commands it may send, and `CommandPolicy` refuses
  anything else before the frame is built. This came directly from reading the
  reference CTI driver, which documents control commands as excluded from
  version 1 and then exposes `pump_on()` and `regen()` methods anyway. Writing
  the rule down did not hold the line. Making the wrong command impossible to
  send does.

- **2026-09-02. The command and the sub-unit address are checked separately.**
  The first version of the policy matched whole command strings. A CTI-style
  terminal addresses pumps as `P` plus two digits plus the command, so twenty
  addresses and eight read commands would have needed one hundred and sixty
  entries in the allowed list, maintained by hand. Nobody maintains that, and a
  safety gate nobody maintains is not one. Now the command is checked against
  the allowed list and the address against a separate list of sub-units, so the
  same device needs eight entries and a range.

- **2026-09-02. The safety gate can be bypassed, and that is written down rather
  than engineered away.** A driver that calls `transport.exchange` directly
  skips the policy. Closing it structurally meant either a transport that only
  talks to a Device, which is hard to test, or a token passed between them, which
  is machinery a beginner has to learn before writing a driver. The chosen answer
  is that every driver sends through `Device.query`, this is stated in the read
  me, and it is the first item in `REVIEW.md` for the critical pass to check.

- **2026-09-02. Banned commands carry their reason in the code.** A refusal that
  says why is worth more than one that just fails. The `g` lockout command on the
  CTI terminal is the example: refusing it is useless if the next person does not
  learn that it cuts the tool's own software off from its pumps.

- **2026-09-02. Silence is retried. A broken reply is not.** Silence usually
  means a busy device or a dropped frame, and one second later it often works.
  A reply that arrived and failed its checksum means the link or the port
  settings are wrong. Sending the same command two more times only writes the
  same failure to the log three times.

- **2026-09-02. A stale reading keeps its last good value and its age.** Blanking
  the screen throws away information. A number from forty seconds ago is still
  useful as long as the screen says how old it is.

- **2026-09-02. A stale reading writes an empty cell to the CSV, never a value.**
  The opposite of the rule above, and on purpose. A screen can explain that a
  number is old. A CSV column cannot. Repeating the last value would invent a
  flat line that never happened, and any average built on the column would be
  wrong. The trend file holds only what was really measured at the time on the
  row.

- **2026-09-02. Polling has a floor of ten seconds a sweep.** Polling harder does
  not produce better trends. It produces a busier device and more chance of
  colliding with the tool's own software. A driver may ask to go slower. Going
  faster takes a deliberate change to `MINIMUM_INTERVAL_S` that someone reviews.

- **2026-09-02. The transport does not open the port itself.** It is handed an
  already-open serial object. That keeps it testable with the mock, and it means
  the caller sets the port parameters, which vary more than you would expect. The
  CTI terminal wants 7 data bits with even parity, where almost everything else
  wants 8 with none.

- **2026-09-02. `pyserial` is imported inside the function that needs it.** The
  core layer is then importable and testable on a machine with no pyserial at
  all, which is what the GitHub runner is.

- **2026-09-02. The poller is a plain loop, not a thread.** The reference project
  describes a poller thread. A synchronous `sweep()` plus `run_forever()` is
  easier to read, easier to test, and enough for a trend tool. Threads can come
  when a UI needs to stay responsive, and `SerialTransport` already holds a lock
  for that day.

- **2026-09-02. Packages are added in the change that first imports them.**
  `pyserial` is pinned now. `pymodbus` waits for the Watlow driver and `secsgem`
  waits for the SECS/GEM monitor. Nobody should be asked to approve a wheel that
  nothing imports.

- **2026-09-02. A release of this library is one zip of the whole project.**
  The code, the tests, and the documents. It is not a tool a person
  double-clicks. It is a folder you put on a bench machine and leave running, so
  the tests and the safety documents travel with it. This shape is provisional.
  It was chosen so the release workflow could be finished, and it should be
  revisited once something actually runs on a bench.

- **2026-09-02. Releases are tagged per project.** `fab-drivers-v0.1.0` and
  `alarm-pareto-v1.5.0`. The repository already had five releases, v1.0.0 to
  v1.4.0, all of them alarm_pareto from before the split. Its numbering carries
  on unbroken, so only the tag name changed and nothing published was disturbed.

- **2026-09-02. `CLAUDE.md` now exists, and holds working instructions.** The
  ten drivers are built one per session, and a session starts with no memory of
  the ones before it. Claude Code reads `CLAUDE.md` automatically, so the
  standing brief lives there: the build order, the rules that do not bend, what
  a driver session produces, and what to check before finishing. The decisions
  log stayed in this file, which is why the two are separate.

- **2026-09-02. Each driver gets its own trend page, not one combined page.**
  Decided by the project owner. The shared generator lives in
  `core/trend_page.py` so the ten pages are one design rather than ten, and a
  driver only says what to plot.

- **2026-09-02. A trend page carries its own data and fetches nothing.** The
  readings are written into the file when it is built. Two reasons. These
  machines have no internet, and a browser opening a file from disk will not
  load a neighbouring file anyway, so a page that read the CSV at view time
  would show nothing at all. A test asserts the page has no external
  references, so this cannot rot quietly.

- **2026-09-02. A gap in the data is drawn as a break in the line.** Joining
  across a gap invents readings that were never taken. It is the same mistake as
  writing the last value into the CSV, one layer further on. A single reading
  between two gaps is drawn as a dot, because a one point line is invisible and
  the reading would silently vanish.

- **2026-09-02. The repository is licensed BSD 3-Clause, held personally.**
  Chosen by the owner. The notice line carries a placeholder until the exact
  name is supplied.

- **2026-09-02. Manuals are fetched out of band, by a separate session, and are
  not committed.** The machines these driver sessions run on cannot reach the
  manufacturers' websites. The network policy allows source and package hosts
  and almost nothing else, so `lakeshore.com` and every mirror of its manuals is
  refused. A session cannot fetch its own sources, and the research rule is not
  negotiable, so the documents have to arrive by hand. `manuals/FETCH_PROMPT.md`
  is the prompt that collects them, written to be handed to a session that does
  have access. The PDFs themselves stay out of git, because they are the
  manufacturers' copyrighted documents. Each `PROTOCOL.md` records its manual's
  part number and SHA-256 instead, so a later reader can tell whether they are
  holding the same document.

- **2026-09-02. A vendor's own driver source is not a substitute for the
  manual.** Lake Shore Cryotronics publishes a Python driver on GitHub and PyPI,
  and GitHub is reachable from here when `lakeshore.com` is not. It contains the
  serial settings and the query strings, and it is written by the manufacturer,
  so it is tempting. It was not used to write anything. Two reasons. It is
  undated with respect to firmware and says nothing about which models or
  revisions each choice applies to, and it does not carry the worked examples
  that settle what a reply actually looks like. The rule asks for a document
  that shows a command next to its real answer, and source code is not that.
  It stays useful as a cross-check once the manual is in hand, and disagreement
  between the two is worth writing down.

## Open questions
1. **Which machine runs the poller long term?** The existing heat exchanger
   Raspberry Pi logger is mentioned for the chiller. If that becomes the home for
   all of it, the CSV location and the port naming should match what is already
   there.

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

## Open questions

1. **The CTI checksum is verified. The rest of the reference is not fully built.**
   The supplied project has the transport and device layers, but no mock class,
   no service layer, and no UI, though its own `CLAUDE.md` describes all three.
   Does the CTI driver get ported into `devices/cti_cryo` as the first real
   driver, using this core, or does it stay a separate program?
2. **What does a release of this library contain?** The alarm_pareto project
   ships as a zip of a tool a person runs. A driver library is closer to
   something you deploy on a bench machine and leave running. That shape needs
   deciding before the first release tag.
3. **One trend page for all devices, or one per device?** The prompt asks for one
   combined page. That is a service layer and UI decision, still to be made.
4. **Which machine runs the poller long term?** The existing heat exchanger
   Raspberry Pi logger is mentioned for the chiller. If that becomes the home for
   all of it, the CSV location and the port naming should match what is already
   there.

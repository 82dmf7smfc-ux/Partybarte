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

- **2026-09-02, later the same day. Reversed: research the web directly.**
  Decided by the project owner. The rule below, that documents are only ever
  supplied, lasted a few hours and was withdrawn because it stopped work dead
  when the owner needed a driver for a demo. Sessions now search for manuals,
  download them and read them. The owner may also hand over a PDF or a compiled
  research file, and those count as sources too.

  What survived the reversal is the part that was actually doing the work.
  **Say what each fact was taken from, and how strong that source is.**
  `PROTOCOL.md` names its sources and ranks them. Anything resting on something
  weaker than a manual goes in `REVIEW.md` as unverified, item by item.

  That is the real safeguard, and it is worth separating from the rule it was
  bundled with. A driver built on a weak source is often the only thing
  available in the time there is, and it is useful. A driver built on a weak
  source that reads as though it came from the manual is not, because nobody
  goes back to check it. Blocking the work was never what made the difference.
  Labelling it is.

- **2026-09-02. Superseded. Outside documents are supplied by the owner, never
  fetched by the session doing the work.** Kept here because a reversed decision
  is worth reading next to the one that replaced it. Decided by the project
  owner, and it held at every stage of every project. A session that needed a
  manual, a register map, a specification or a standard it did not have wrote a
  fetch prompt, handed it over as a file, and stopped.

  The practical reason is that these machines cannot reach the manufacturers'
  websites, and rediscovering that every session is waste.

  The real reason is what happens next when fetching is hard. The substitutes
  are all within reach: a search snippet, a summary site, a forum answer, a
  vendor's own driver source, or memory of a protocol that resembles this one.
  Each of them produces code that looks finished and was never checked. The rule
  removes the temptation by removing the choice, which is the same reasoning as
  the read-only allowed list. Writing a rule down did not hold the line there
  either. Making the wrong move impossible to reach does.

  One distinction is kept deliberately. Searching for candidate links is allowed,
  because a fetch prompt carrying exact URLs saves the owner a hunt. Reading a
  search result for the answer is not. The line is that a link is a lead and a
  snippet is not evidence.

- **2026-09-02. The manuals live in `manuals/` and are not committed.** They are
  the manufacturers' copyrighted documents and some are large, so `.gitignore`
  keeps the PDFs out. What is committed is the fetch prompt and the manifest
  that arrives with a delivery, because those record where each document came
  from, its part number and its SHA-256. Each `PROTOCOL.md` names its manual and
  repeats the hash, so a later reader can tell whether the document in their
  hands is the one the driver was written against, and a reviewer can tell that
  a manual was really read rather than assumed.

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

- **2026-09-02. One Lakeshore driver for all three models, not three drivers.**
  The 218, 224 and 336 send the same ASCII commands with the same carriage
  return and line feed terminator, and the same reply format. What differs is
  the port speed and what the sensor inputs are called. That is a table, not
  three classes. `LakeshoreMonitor` takes a model name and looks the differences
  up in `MODELS`. Three classes would have shared everything except two
  constants and would have drifted apart the first time one was fixed.

  The model has to be given, not guessed. `identify()` reads `*IDN?` so a caller
  can check the instrument matches, and that check is the caller's to make. A
  218 driver pointed at a 336 addresses inputs 1 to 8, which do not exist there.

- **2026-09-02. Ethernet is out of scope for version 1.** The 224 and the 336
  both have it, on TCP port 7777, speaking the same ASCII as the serial port. It
  was still left out, and no socket was bolted into the driver.

  The reason is that it turned out not to be needed. Neither model has a DE-9
  socket at all. Their USB ports enumerate as virtual COM ports, so
  `SerialTransport` already reaches every one of the three instruments. Adding a
  socket transport would have been a change to shared code that all ten drivers
  inherit, to reach hardware that is already reachable.

  When Ethernet is wanted it belongs in the core, as a second transport with the
  same `exchange` method, not in this driver. `PROTOCOL.md` carries the two
  facts that work will need: a 336 accepts at most two simultaneous sockets, so
  a stuck connection can lock out reconnects, and the VISA resource form
  `TCPIP::<address>::7777::SOCKET` is reported to work.

- **2026-09-02. `CommandPolicy` grew an `untargeted` list.** The first driver
  found a gap in the core on its first day. A Lakeshore has sub-units, its
  sensor inputs, so `targets` is set. But `*IDN?` asks the box who it is and
  there is no input to name. `check_target` refused it, because with `targets`
  set it required every command to carry one.

  The two ways round it without touching the core were both bad. Inventing an
  address that means "the instrument itself" puts a fake sensor in the allowed
  list. Letting any command go untargeted stops the check catching a missing
  address, which is most of its value. So the policy now takes the small list of
  commands that are aimed at the box rather than at a sub-unit, and checks them
  accordingly. Every later driver gets it, and most of the ten will need it,
  because an identity query is nearly universal.

- **2026-09-02. Every temperature is read with its status, or not at all.**
  This is the one thing about these instruments most likely to catch somebody
  out. A sensor that is unplugged, shorted or off the end of its curve does not
  go silent. It answers `KRDG?` with a number. Only `RDGST?` says the number
  means nothing.

  So `read_checked_kelvin` asks `RDGST?` first and returns None when it is
  nonzero, and `read_all_kelvin` does the same for every input. It costs a
  second query per reading. That is the right trade at a ten second polling
  floor. The alternative is a trend that shows a cold head sitting at exactly
  zero kelvin for a week, which is both obviously wrong and easy to miss,
  because a flat line at the bottom of a chart looks like a stable cold head to
  anybody glancing at it.

- **2026-09-02. `*CLS` is banned along with `*RST`.** `*RST` is obvious: it
  throws away the sensor configuration. `*CLS` is the interesting one. It only
  clears the status registers, it is not a machine control action, and it is
  widely suggested as a harmless way to wake an instrument that is not
  answering. It was banned anyway. It destroys state the tool's own software may
  be waiting to read, and version 1 reads. An instrument that will not answer is
  a port settings problem or a power cycle, not something to clear.

  The research file records a forum case where a 218 only answered `*IDN?` after
  an `*RST`. That is exactly the situation where somebody reaches for one of
  these, and it is why the reason is written next to the ban rather than left to
  be worked out.

- **2026-09-02. A trend page column can be drawn on a log axis, and the choice
  lives in the shared generator.** Pressure runs from atmosphere down to 1e-9
  torr. On a linear axis every reading below about 1 torr sits on the bottom
  pixel of the chart, so the whole of a pumpdown after the first few seconds is
  a flat line along the bottom edge. Measured on a real sample: five decades of
  pumping landed inside five pixels of a 180 pixel chart. The Lakeshore driver
  never met this, because temperature spans one decade and not nine.

  `render_trend_page` and `write_trend_page` now take a `scales` dictionary of
  column name to `"linear"` or `"log"`. A column nobody mentions stays linear.
  It went in the shared generator rather than in this driver because three of
  the ten planned drivers read pressure, and because `CLAUDE.md` says directly
  that a device needing something the generator cannot do is a reason to improve
  the generator.

  A misspelled column name in `scales` raises rather than being ignored.
  Ignoring it would leave the chart linear with nothing on the page saying so,
  which is the exact silent wrongness this library exists to avoid.

- **2026-09-02. A zero or negative reading on a log axis becomes a gap, and the
  page says how many.** There is no logarithm of zero, and a gauge that is
  switched off may well report exactly zero. Three things were possible: drop
  the reading silently, clamp it to the bottom of the axis, or turn it into a
  gap. Clamping invents a pressure that was never measured. Dropping it silently
  loses the fact that a reading came back at all. So it becomes a gap, which
  breaks the line under the existing gap rule, and the count is printed under
  the chart. The number is the part that matters: a chart with forty gaps in it
  is telling you something about the gauge, not about the logger.

- **2026-09-02. The summary table switches to scientific notation outside a
  band.** `_tidy_number` printed `%.2f`, so 1e-9 torr showed as `0.00` and every
  pressure column in the summary was useless. Below 0.01 or at or above 100000
  it now prints `%.2E`. Temperatures and flows are untouched, which is what
  keeps the Lakeshore page reading the way it did.

- **2026-09-02. The gauge address is a `CommandPolicy` target, and the gauge
  selector is not.** These instruments put a two character hexadecimal address
  in every frame, right after the `#`. That is the bus address, and it is what
  `targets` is for, so it is checked separately from the command and never
  folded into the command string.

  A Series 350 controller then has four gauges behind that one address, chosen
  by a modifier: `RD 1`, `RD 2`, `RD A`, `RD B`. Those modifiers stay part of
  the command, and the reason is that the manual's own description of the frame
  treats them as one. Its words are "a start character, an address, a command,
  and a command modifier". The address says which box on the pair is being
  spoken to. The modifier says what is being asked of it. Two levels, and only
  the outer one is an address.

  The list stays small either way. A 350 needs six allowed entries and thirty
  two addresses, not one hundred and ninety two combinations.

- **2026-09-02. The driver checks the address the instrument echoed back.**
  Every reply carries the address it came from. The driver compares it with the
  address it sent and raises if they differ. This costs nothing and it catches
  the RS-485 failure that has no other symptom: on a shared pair every module
  hears every frame, so a second module answering hands you a perfectly
  plausible pressure belonging to the wrong gauge. Silence you notice. A wrong
  number attached to the right column you do not.

- **2026-09-02. Version 1 talks to one gauge at a time, not to a multi-drop
  bus.** RS-485 can carry several modules on one pair. This driver does not
  support that, and saying so plainly is better than leaving it to be
  discovered. One `GranvillePhillipsGauge` instance holds one address, and the
  core owns one device per transport.

  Two reasons. The core's `SerialTransport` guarantees one exchange at a time on
  one port, but nothing in it knows about the turnaround delay a shared pair
  needs between one module releasing the line and the next one driving it, and
  no source found here says what that delay is. And nothing in this project has
  ever driven a real RS-485 pair, so the first multi-drop bus would be debugged
  with untested code on live equipment.

  The address check above is what makes this safe rather than merely limited. If
  somebody does wire two gauges to one pair and points two drivers at them, a
  crossed reply raises instead of being trended.

- **2026-09-02. `units` has no default, because these instruments will not say
  what they are set to.** They can report torr, mbar or pascal, the setting
  lives in the instrument, and the reply carries a bare number. A read-units
  query was searched for specifically and none was found in any source. Set-unit
  commands exist and are banned.

  So the caller has to state the unit, and it goes into the trend column name.
  A default of torr would have been convenient and would have produced exactly
  the failure the session brief warns about: a file whose units change halfway
  through, where the numbers stay plausible on both sides of the change.

  This does not fix the problem. Somebody who changes the units on the front
  panel and not in the code still gets a wrongly labelled file. It only makes
  the assumption visible at the point it is made. The real fix needs a query
  that appears not to exist, and that is written up in `REVIEW.md`.

- **2026-09-02. A reading of 9.99E+09 is a hole, not a pressure.** The manuals,
  relayed, say `RD` returns `9.99E+09` for the first three to five seconds after
  power up, and by every account it is also what a gauge that is off reports.
  The driver treats anything at or above 1e9 as no reading.

  This is the Lakeshore lesson from the other side. There, a dead sensor
  answered with a plausible number and only a second query said it was
  meaningless. Here the instrument does say so, but it says so in the shape of a
  number, and a driver that does not know the convention will plot 9.99e9 torr
  next to 1e-6 torr and flatten the chart. The threshold is safe with a wide
  margin: atmosphere is about 760 torr, so nothing real comes within six decades
  of it.

- **2026-09-02. The Series 375 is shipped with its channel handling marked
  unsourced, rather than left out or guessed at.** It is a multi-channel
  controller and nothing found here says how to ask it for one channel. Leaving
  it out would have dropped a device the session asked for. Inventing a selector
  would have produced exactly the plausible-looking syntax the brief forbids.

  So the 375 sends the bare `RD` the single gauge modules use, and
  `ModelProfile` carries a `sourced` flag that `describe_sources()` prints. A
  warning that only lives in a markdown file is one nobody reads at the bench.
  Whoever holds the 375 manual should settle this in ten minutes.

- **2026-09-02. The core transport learned to read a reply by its length, not
  by a terminator.** This is the first shared-code change a driver has forced,
  and eight more drivers inherit it, so it is written up here in full.

  `SerialTransport` read up to a terminator, usually a carriage return. That
  works for every ASCII protocol and cannot work for a binary one. Any byte
  value can appear in a payload, so there is no byte left over to mean "the
  frame ends here". A `\r` inside a checksum would cut a frame in half, and the
  half left in the buffer would be read as the front of the next reply.

  What binary protocols have instead is a length. The chiller writes the number
  of data bytes at index 4, so the whole frame is `6 + n` bytes.

  So `SerialTransport` grew one optional argument, `reply_size`. It is a
  function the driver supplies. Given the bytes that have arrived so far it
  returns the total frame length, or `None` for "I still cannot tell". The
  transport reads a byte at a time until it can tell, then asks for exactly the
  rest.

  Three things about the shape of it were deliberate.

  It is optional and defaults to `None`, so the nine drivers that read up to a
  terminator behave exactly as they did. A test asserts that.

  It is a function rather than a fixed offset, because the next binary drivers
  do not agree on where the length lives. Modbus RTU derives it from the
  function code, AE Bus packs a length into the low bits of a header byte. A
  number would have covered this device and nothing else.

  It stops at the declared length rather than draining the buffer. That is the
  bug worth naming: read one byte too many and the next exchange starts on
  somebody else's last byte, and every reply from then on is off by one while
  still looking like data. There is a test for exactly that.

  `MockSerial` grew `read(n)` to match, returning what is there when less is
  there, which is what a real port does when it times out mid-frame.

- **2026-09-02. `parse_reply` returns a structure for this driver, and the base
  class did not change.** The two earlier drivers return text and turn it into a
  number in a separate step. A binary protocol has no text stage.

  The checking has to happen in `parse_reply`, because that is where `core/device.py`
  says a driver checks its checksum, and because a corrupted frame must never
  become a number. But what the data bytes mean depends on which command was
  asked: three bytes are a measurement, four or five are the fault bits, two are
  a protocol version. So returning a number was not possible and returning bytes
  would have thrown away the checking.

  `parse_reply` therefore returns an `NcReply`: the frame unwrapped, with the
  checksum, the error command, the lead character and the echoed address already
  checked. The caller reads the part it wants.

  **The base class needed no change at all.** `Device.parse_reply` already
  returns whatever the driver wants, and this was checked before touching shared
  code rather than after.

- **2026-09-02. The checksum was proved against nineteen frames printed in the
  manuals before it was trusted.** Two Thermo NESLAB manuals were read directly,
  which is a first for this project, and between them they print nineteen
  complete frames with their checksums. Every one is a parametrised test.

  This was worth the effort for a specific reason. The mock also computes
  checksums, and a mock that shares the driver's arithmetic will agree with a
  broken driver and prove nothing. So the mock computes its checksums with its
  own code, deliberately duplicated, and the manual's own bytes are what decides
  which of them is right.

  **Eighteen agree. One does not.** The Digital Plus manual prints Read Cool
  Proportional Band as `CA 00 01 74 00 84`, and the manual's own stated rule
  gives `8A`. The one independent implementation found also sends `8A`. It is
  almost certainly a misprint. The driver computes every checksum and copies
  none, so it sends `8A`, and the disagreement is a test of its own so that
  anybody changing the checksum has to come and look at it.

- **2026-09-02. Neslab and ThermoFlex are one class, because they are one
  protocol.** The session brief asked for this to be checked rather than
  assumed, on the grounds that two genuinely different protocols in one class
  with a flag is how a driver becomes unreadable. It was checked.

  They share the framing, the checksum, the address bytes, the two lead
  characters, the error replies, the qualifier byte layout, and the command
  bytes for temperature, setpoint and the temperature limits. A working
  ThermoFlex library builds `[0xCA, 0x00, 0x01]` frames with the NESLAB
  checksum, which is the NESLAB manual's protocol exactly.

  What differs is which registers exist behind it, and what the fault bits mean.
  A ThermoFlex has a pump, so it has flow and pressure to read and a bath does
  not. That is a capability list, not a second protocol, and `ModelProfile`
  already existed to hold exactly that, from the Granville-Phillips driver.

  **What would reverse this.** If a bench visit shows a ThermoFlex framing a
  message differently, or computing its checksum over a different range, split
  the class. Different command bytes would not be enough on their own, and
  neither would the different status tables, which are already two separate
  named tables rather than a flag inside one.

- **2026-09-02. Reading a setpoint is allowed. Writing one is banned twice
  over.** These are one bit apart. Read Setpoint is command `70` and Set
  Setpoint is command `F0`, and the manual's Table 1 separates them into a READ
  block and a SET block.

  Reading it is worth having, because a chiller drifting from its setpoint is
  the fault a trend exists to catch, and you cannot see the drift without both
  numbers. Writing it changes the temperature of the water feeding live
  equipment.

  So the read is on the allowed list and the write is on the banned list with
  its reason. That is the same protection every other driver has.

  This device got a second one as well. Every write command in both manuals has
  bit 7 set and every read command does not, across the whole of both tables.
  `build_frame` refuses any command byte at or above `0x80` outright. That is an
  observed regularity and not a rule either manual states, so it is written down
  as such, and it is a second line of defence rather than the first. What it
  catches is a future session adding something to an allowed list without
  reading `PROTOCOL.md`, which is a likelier failure than the policy itself
  going wrong.

- **2026-09-02. A reading in the wrong unit is refused, not converted.** Unlike
  the Granville-Phillips gauges, this instrument states its unit in every single
  reply. That is a gift and the driver spends it: each command says what unit it
  expects, and a reply in any other unit raises instead of being converted.

  Converting quietly would put two units in one trend column with every number
  in it plausible, which is the failure the gauge driver could only make visible
  and not prevent. Here it can be prevented, so it is.

- **2026-09-02. The shared trend generator learned to draw two lines on one
  chart.** A reading and the setpoint it is holding were on separate charts, and
  the page was generated and looked at, which is how this was caught.

  Separate charts cannot answer the question a setpoint is for. Each chart
  scales itself to its own readings, so a setpoint that has not moved all week
  fills its chart from top to bottom exactly as much as a temperature that has
  climbed five degrees. Both look flat, or both look dramatic, and the gap
  between them is nowhere on the page.

  So `render_trend_page` grew an `overlays` argument, and `_chart_svg` now takes
  a list of series sharing one axis. The second line is drawn in another colour
  **and** dashed, so it survives a black and white printout and a reader who
  cannot separate the two colours.

  It went in the shared generator rather than in this driver because a value and
  its setpoint is not a chiller thing. The Watlow heater zones have it too. The
  brief says to improve the generator rather than work around it, and this is
  what that looks like.

  Two lines, not three. A chain of overlays raises, because three lines on one
  axis stops being readable and a chain is a way of asking for three without
  noticing.

## Open questions
1. **Which machine runs the poller long term?** The existing heat exchanger
   Raspberry Pi logger is mentioned for the chiller. If that becomes the home for
   all of it, the CSV location and the port naming should match what is already
   there.

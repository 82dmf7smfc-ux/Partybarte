# SCOPE.md, Stage 0 output

Schema version: 3.3
Reader version: 3.3.1
Written: session 1

## How this was researched

Public sources only. This session ran inside a sandbox whose network policy
blocked direct page fetches to appliedmaterials.com, patents.google.com,
uspto.gov, freepatentsonline.com, pmc.ncbi.nlm.nih.gov and every other site
tried. Web search worked. So every source below was reached through search
result titles, URLs and search-engine summaries, not by reading the page.

That is recorded per source in `sources.csv` as `access=snippet-only`. Anything
resting only on a snippet is capped at `probable`, never `established`. The
first job of session 2, on an unrestricted network, is to open the snippet-only
sources and either confirm or correct what is written here.

## Tool identity, settled

- Polisher core: three polishing platens, four wafer carriers on a rotating
  carousel, one to three polishing steps [sst-new-cmp-architecture].
- The carousel lets the handling robot load and unload at a transfer station
  while the platens keep polishing [sst-new-cmp-architecture].
- Base Mirra is dry-in and wet-out [sst-new-cmp-architecture].
- Mirra Mesa is the same polisher made dry-in and dry-out by the integrated
  Mesa cleaner [amat-mirra-mesa-200mm].
- Wafer sizes 150 mm and 200 mm, both configurations offered
  [entrepix-mirra].
- Applications named by public sources: silicon, shallow trench isolation,
  oxide, polysilicon, tungsten, copper damascene [entrepix-mirra].
- Applied Materials names Titan Head carriers and precise endpoint detection as
  part of the architecture [amat-mirra-200mm].

## The five Stage 0 questions

### 1. Head generations, what shipped when and what differs

Partly answered.

One conference paper on head upgrades describes three head types by zone count.
Titan is a three zone membrane carrier with front referencing, a flat edge to
within 3 mm, and some edge tuning. Profiler is a four zone head giving increased
edge tuning. Contour is a six zone head giving full radial control
[ieee-profiler-contour-heads]. The same work ties Profiler to 150 mm and Contour
to 200 mm, and reports that both removed the need for daily process
qualification and for the per lot look-ahead step
[ieee-profiler-contour-heads].

Not answered: which generation shipped when. No date, revision level or product
timeline was found in any public source reached. Also not answered: whether a
200 mm Profiler was offered.

Routing: research. The zone counts need confirming from the paper itself or from
an Applied Materials document. Zone count on the tool in front of you is
routing on-tool, by counting pressure lines or reading the service screen.

### 2. The Mesa cleaner wafer path

Partly answered.

Applied Materials describes the cleaner as configurable with up to four separate
process modules: a single wafer immersion megasonic module, two double sided
brush scrubber stations, and a spin rinse dryer [amat-mirra-mesa-200mm]. The
integration is described as a four step cleaning process giving dry-in and
dry-out operation [amat-pr-mirra-mesa]. Wafers are gripped at the edge and
submerged vertically, and are cleaned on both faces [amat-mirra-mesa-200mm].

Not answered: the station order, beyond the dryer being last by function. Not
answered: which of those stations exist on the 150 mm version. No public source
reached addresses the 150 mm cleaner at all.

Note the wording. Up to four modules is a configuration maximum, not a
description of every tool. A Mesa with one brush station is still a Mesa.

Routing: on-tool. The station set and order are visible on the machine.

### 3. Endpoint options and which platens carry them

Partly answered.

Applied Materials states that its optical endpoint methodology is available on
Mirra, Mirra Mesa and Reflexion systems [amat-pr-optical-endpoint]. The method
puts a laser interferometer in the platen, sends the beam through a transparent
window in the pad, and reads light reflected from the wafer
[amat-pr-optical-endpoint]. The in-situ rate monitor determines endpoint from
periodic optical interference changes, filtered so intensity cycles with
thickness removed [pat-us6537133].

Motor current endpoint is a standard CMP technique [rev-zantye-2004]. No source
reached here confirms it as an offered Mirra option, so it is recorded as a
general CMP signal and not as a Mirra feature.

Not answered: which platens carried the optics, and whether it was one platen or
all three.

Routing: on-tool for this tool. Research for the platform.

### 4. What changes between 150 mm and 200 mm

Not answered.

The search for configuration differences returned nothing usable. Public sources
confirm both sizes were offered [entrepix-mirra] and nothing more. The one
indirect hint is that the head study names Profiler for 150 mm and Contour for
200 mm [ieee-profiler-contour-heads], which may mean head options differed by
wafer size, or may only reflect what that study happened to cover. Do not treat
it as evidence.

Routing: on-tool where the tool can be inspected. Research otherwise.

### 5. What is genuinely unknowable from public sources

Best judgement after one session. Each of these should be confirmed as a dead
end rather than assumed:

- Recipe parameter ranges and limits: zone pressure limits, platen and head
  speed limits, ring load ranges.
- Alarm codes, error text, and control software behaviour. This is expected to
  stay the weakest branch.
- Service screen contents and calibration procedures.
- Consumable part numbers, pad and membrane and ring change intervals.
- Throughput figures per configuration.
- Anything about custom or modified tools, by definition.

Facilities figures, footprint and utility requirements were not searched yet and
may still be findable in a used-tool datasheet. That is research, not unknowable.

## Excluded products

These share a name or an architecture and will pollute searches. Reject and say
so when a result is about one of them.

- Mirra Trak or MirraTrak, integrated with the OnTRAK Integra cleaner
- Mirra DNS, integrated with the DNS AS-2000 cleaner
- Desica, a different cleaner option using Marangoni drying
- Mirra Durum, the current SiC variant, which dominates live Applied Materials
  pages
- Reflexion and Reflexion LK, the 300 mm successor platform

Search results for Mirra Desica and Mirra Trak appeared in this session's
searches and were rejected on that basis.

## Boundary of the project

Everything past the five answers above is observation, not research, and files
as custom or uncertain. The honest position after Stage 0 is that the
architecture is settled, the head zone counts are probable, the Mesa module list
is probable, and the 150 mm configuration is close to undocumented in public
sources.

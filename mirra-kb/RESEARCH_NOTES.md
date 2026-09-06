# Research notes, session 1

## What this file is, and what it is not

Every source in `sources.csv` was reached through a web search. The pages
themselves were never opened. The session network policy blocked direct fetches
to appliedmaterials.com, ir.appliedmaterials.com, patents.google.com,
image-ppubs.uspto.gov, freepatentsonline.com, pmc.ncbi.nlm.nih.gov,
nccavs-usergroups.avs.org, entrepix.com, semigroup.com, espacenet and
en.wikipedia.org. Every one returned 403 at the proxy or failed to connect.

So what follows is **search-engine summary text**, saved verbatim, together with
the URLs the search returned. It is evidence of what a summary said, not
evidence of what a page says. A summary can paraphrase, compress, merge two
sources into one sentence, or attribute a claim to the wrong document.

Five sources are worse than that, and they are marked `not-retrieved` rather
than `snippet-only`: `ref-preston-1927`, `book-steigerwald-1997`,
`rev-zantye-2004`, `thesis-lai-mit` and `nccavs-feeney-2012`. No summary of their
content was ever seen. The claims citing them are standard CMP knowledge, written
from general understanding and then attributed to the standard source for that
knowledge. That is an attribution by reputation, not evidence. Confirm those
claims against the documents or replace the citations.

Treat every quotation below as a lead to verify, not as a citation. Objective 1
of the next session is to open these URLs and either confirm the claim or
correct the node.

This file exists because that verification is impossible without it. Once the
pages are read, replace the relevant block here with what the page actually
said, and note the correction in `SESSION_LOG.md`.

---

## 1. Mirra head generations

**Query:** Applied Materials Mirra CMP Titan head Titan Profiler carrier head zones
**Outcome:** hit

URLs returned:
- https://ieeexplore.ieee.org/document/7919822/ (Process stability and tool
  capacity improvement with 150mm Profiler and 200mm contour heads)
- https://www.appliedmaterials.com/en-in/products/mirra-mesa-cmp-200mm
- https://www.appliedmaterials.com/us/en/product-library/mirra-cmp-200mm.html
- https://nccavs-usergroups.avs.org/wp-content/uploads/CMPUG2012/cmp2012_7feeney.pdf
- https://www.ebay.com/itm/165874334996 (AMAT 0010-24500 Mirra Titan II Profiler
  200mm CMP polisher HEAD)
- https://www.semigroup.com/wp-content/uploads/2021/09/0010-77533%7CAppliedMaterials200mmMIRRATitan1HEAD.pdf

Summary text, verbatim:

> The Applied Materials CMP system can be equipped with 150mm Titan Profiler or
> 200mm Titan Contour wafer-carrier heads.
>
> The Titan head has a 3-zone membrane carrier that enables front referencing
> technology with flat edge to 3mm and some edge tuning. The Profiler head is a
> 4-zone head that provides increased edge tuning. The Contour head is a 6-zone
> head that provides full radial control.
>
> The process stability with 150mm Profiler and 200mm Contour wafer-carrier heads
> makes daily process qualification unnecessary and enables the elimination of
> the time-consuming look-ahead step for each product lot. The multi-zone
> polishing heads enable superior uniformity and efficiency with low downforce.

**What was written from this:** `titan-head`, `titan-profiler-head`,
`zone-pressure-control`, `within-wafer-nonuniformity`, cited as
`ieee-profiler-contour-heads`.

**Caution.** The summary blends what may be several documents. Zone counts are
recorded on the nodes as probable and the uncertainty is stated in the
`## Contested` sections. Two auction and dealer listings in the same result set
mention "Titan II Profiler 200mm" and "MIRRA Titan 1", which if genuine would
mean a 200 mm Profiler existed and that Titan has numbered generations. Both are
tier 5 leads, neither is cited, and both are worth chasing.

---

## 2. Mesa cleaner

**Query:** Mirra Mesa cleaner brush scrubber stations dry-in dry-out post-CMP clean Applied Materials
**Outcome:** hit

URLs returned:
- https://ir.appliedmaterials.com/news-releases/news-release-details/applied-materials-announces-new-mirra-mesa-system-address-market/
- https://ir.appliedmaterials.com/news-releases/news-release-details/umc-orders-multiple-applied-materials-mirra-mesa-cmp-systems-new
- https://patents.google.com/patent/US6886387B1/en (Brush pressure calibration
  apparatus and method)
- https://www.appliedmaterials.com/en-in/products/mirra-mesa-cmp-200mm
- https://www.semiconductoronline.com/doc/cmp-system-0001

Summary text, verbatim:

> The Mirra Mesa CMP system offers a complete automated dry-in/dry-out post-CMP
> cleaning process that delivers outstanding particle performance.
>
> The Mesa cleaner can be flexibly configured with up to four separate process
> modules: a single-wafer immersion megasonic module for maximum cleaning
> efficiency, two double-sided brush scrubber stations and a spin rinse dryer.
>
> The MIRRA MESA brush scrubber cleaner cleans wafers using a combination of
> rinsing, megasonic rinsing, and brush cleaning. The brush cleaning cycle
> involves rotating the wafer at a specific speed, typically about 1500 rpm,
> while a jet of deionized water is sprayed on the wafer to dislodge any loose
> debris from the CMP process. Simultaneously, the wafer is brushed with a foam
> brush, which rotates at typically about 400 rpm.
>
> For enhanced defect control, wafers are gripped at the edge and submerged
> vertically into the modules where they are cleaned on front and back sides.
>
> By fully integrating a unique four-step cleaning process with the Mirra CMP
> system, the Mirra Mesa provides production-worthy dry-in/dry-out CMP
> processing with designed-in reliability, serviceability and the industry's
> highest wafer throughput per square foot.

**What was written from this:** `mesa-cleaner`, `pva-brush-scrubber`,
`megasonic-clean`, `spin-rinse-dryer`, cited as `amat-mirra-mesa-200mm` and
`amat-pr-mirra-mesa`.

**Caution.** The rpm figures almost certainly come from US6886387, whose assignee
was never confirmed. They are recorded on `pva-brush-scrubber` as a patent
embodiment and explicitly not as a Mesa specification. The rest reads like
Applied Materials marketing copy, which is where the "up to four modules" and
"four-step cleaning process" wording comes from. Nothing here says which modules
a given tool has, or their order.

---

## 3. Endpoint detection

**Query:** Mirra CMP endpoint detection ISRM in-situ rate monitor motor current endpoint platen
**Outcome:** hit

Summary text, verbatim:

> The Mirra CMP device uses an in-situ rate monitor (ISRM) system to determine
> endpoint through the concept of periodic optical interference changes. Signals
> received from a patterned wafer surface are processed by digital filtering
> algorithms such that optical interference intensity changes periodically with
> the thicknesses of removed surface material.
>
> Applied Materials' proprietary In Situ Rate Monitor (ISRM) endpoint technology
> allows real-time monitoring of the CMP process. The ISRM detects film thickness
> changes during polishing for highly accurate, real-time process control that
> allows precise definition of material removal and process endpoint.
>
> Monitoring motor current of the platen tracks the power required to rotate the
> platen based on the coefficient of friction of the surface being polished. When
> polishing a low friction surface like metal the motor current is low, then rises
> as the metal film thickness goes to zero and the polishing pad begins to polish
> the oxide.
>
> Applied Materials developed the Mirra CMP systems with a unique three
> platen/four head architecture for single-wafer control, with improved head
> designs and an in-situ removal monitor (ISRM) contributing to performance.

**Query:** Applied Materials patent Birang in-situ optical monitoring polishing pad window laser interferometry endpoint CMP
**Outcome:** hit

URLs returned:
- https://ir.appliedmaterials.com/news-releases/news-release-details/applied-materials-awarded-key-patent-cmp-endpoint-detection
- https://image-ppubs.uspto.gov/dirsearch-public/print/downloadPdf/6537133
- https://www.edn.com/applied-receives-endpoint-detection-patent/

Summary text, verbatim:

> Applied Materials was granted U.S. Patent No. 6,537,133 entitled "Method for
> In-Situ Endpoint Detection for Chemical Mechanical Polishing (CMP) Operations."
>
> The technology uses a laser interferometer embedded in the tool's platen to
> direct a light beam through a transparent window in the polishing pad and onto
> the wafer, with light reflected from the wafer providing data on the thickness
> of material removed during polishing.
>
> Applied Materials' optical endpoint technology is available on its Mirra, Mirra
> Mesa and Reflexion CMP systems.
>
> Birang, M. (along with Chan, D. A., Swedek, B., and Wiswesser A.) published work
> in 1998 titled "Process Control and Monitoring with Laser Interferometry Based
> Endpoint Detection in Chemical Mechanical Planarization".

**What was written from this:** `endpoint-detection`, `isrm`,
`motor-current-endpoint`, cited as `pat-us6537133`, `amat-pr-optical-endpoint`,
`amat-mirra-200mm`.

**Caution.** Note the two different expansions of ISRM in the first summary, "in
situ rate monitor" and "in-situ removal monitor". That is recorded as a contested
naming on the `isrm` node. The patent text itself was never read. The Birang 1998
paper is an uncited lead worth chasing, and would be a tier 2 or 3 source for the
optical method.

---

## 4. Polisher architecture

**Query:** "Mirra" CMP "three platen" "four" carrier head carousel 200mm architecture description
**Outcome:** thin

URLs returned:
- https://go.gale.com/ps/i.do?id=GALE%7CA17974893 (New CMP architecture addresses
  key process issues, Solid State Technology, ISSN 0038111X)
- https://www.entrepix.com/amat-mirra
- https://moov.co/marketplace/cmp/amat-applied-materials/amat-applied-materials-mirra/
- https://www.bridgetronic.com/products/68347 (Applied Materials Mirra 3400)

Summary text, verbatim:

> The Mirra system incorporates a rotating four-head "carousel" design that allows
> the wafer handling robot to transfer wafers to a load/unload station while the
> three platens operate continuously.
>
> The Applied Materials Mirra CMP Tool is a Dry In - Wet Out (DI-WO) type of CMP
> machine which incorporates three polishing platens, and the four wafer carriers
> are supported by a carousel transfer mechanism that moves the wafers through a
> one, two, or three step polishing process.
>
> The Mirra system, which is available for 200mm and 300mm wafer sizes, utilizes a
> unique multi-platen architecture, Titan Head(TM) wafer carriers and precise
> endpoint detection technology to deliver superior process performance and
> throughput.
>
> The AMAT CMP polisher will process wafers from 150 to 200mm in diameter, and can
> be used for the planarization of thin films such as oxide, tungsten, and
> Polysilicon.

**What was written from this:** `carousel`, `platen`, `carrier-head`, `slurry`,
`polishing-pad`, cited as `sst-new-cmp-architecture` and `entrepix-mirra`.

**Caution.** This is the weakest sourcing in the base and the reader flags
`carousel` for it. Everything above is trade press or dealer copy. The line about
300 mm is a good example of why: it likely refers to Reflexion, an excluded
product, or is simply wrong. It was not used. A tier 1 or tier 2 source for the
three platen and four head architecture is objective 3 of the next session.

Note also "Mirra 3400" appearing as a dealer model designation. If that is a real
Applied Materials model number it is worth knowing, and it is not cited anywhere.

---

## 5. Physics spine sources

**Query:** Preston equation CMP removal rate MRR = Kp P V origin 1927 glass polishing
**Outcome:** hit

> The Preston equation states: Material removal rate (MRR)=Kp*V*P where V is the
> velocity of the polishing pad surface with respect to the substrate surface
> being polished, P is the pressure applied to a radial zone of a wafer to be
> polished against the polishing pad, and Kp is a proportionality constant known
> as the Preston coefficient.
>
> Long ago, Preston empirically found in glass polishing that the material removal
> rate (MRR) is proportional to the product of the applied pressure and the
> relative velocity (Preston, 1927). Originally proposed for glass polishing, the
> Preston equation is also of an empirical nature and lacks scientific basis.

Used for `preston-equation` and `removal-rate`. URLs included
https://link.springer.com/article/10.1557/s43578-020-00060-x and
https://web.mit.edu/cmp/publications/thesis/jiunyulai/ch2.pdf. The 1927 paper
itself was not located, so `ref-preston-1927` carries `url=na` and
`access=not-retrieved`.

**Query:** CMP Stribeck curve lubrication regime hydrodynamic boundary contact mode Sommerfeld number polishing
**Outcome:** hit

> The lubrication in CMP can be determined by the Stribeck curve since it provides
> direct evidence of the extent of contact among wafer, pad asperities, and slurry
> particles.
>
> Three major areas of the Stribeck curve can be distinguished: boundary
> lubrication at small Sommerfeld numbers where all solid bodies are in intimate
> contact with each other, mixed lubrication where the wafer and pad are not in
> intimate contact but some abrasives remain in contact and a thin fluid film
> about the thickness of the roughness of the pad forms, and hydrodynamic
> lubrication at large Sommerfeld numbers wherein the fluid film between pad and
> wafer is larger than the roughness of the pad.
>
> In the region indicated as "boundary lubrication", both the polishing pad and
> the substrate are in intimate contact with slurry abrasive particles, and COF
> remains constant with increasing values of Sommerfeld number. In this regime
> larger values of both the COF and removal rate (RR) are obtained.
>
> The Sommerfeld number (So) is given by So[=uV/(p deff)] where u=slurry
> viscosity, V=the relative pad-wafer velocity, p=pressure; and
> deff=aRa+[1-a]dgroove where Ra=average pad roughness, dgroove=pad groove depth.

Used for `lubrication-regime` and `pad-asperity-contact`, cited as
`intech-cmp-lubrication` (https://www.intechopen.com/chapters/52631).

**Query:** CMP pad grooving slurry transport mean residence time under wafer flow rate effect removal rate
**Outcome:** hit

> Slurry MRT represents the average time it takes for fresh incoming slurry to
> replace the existing slurry in the region bound between the pad and the wafer.
>
> Mean removal rates measured using a reflectometer were 1655, 1613 and 1551
> Angstroms/minute at 200, 150 and 100 cc/min flow rates, respectively.
>
> Results showed that MRT and efficiency increased significantly when the groove
> width increased from 300 to 600 um. MRT was reduced at a higher polishing
> pressure.
>
> Slurry transport efficiency depended on platen speed, flow rate, and the
> conditioning method.

Used for `slurry-transport` and `polishing-pad`, cited as `sd-groove-width-mrt`
and `sd-groove-flow-numerical`.

**Query:** planarization length pad bending stiffness step height reduction CMP pattern density model
**Outcome:** hit

> In the effective density model, planarization length is the characteristic
> length of an elliptic weighting function based on the long-range pad deformation
> and pressure distribution during CMP. One definition is a circle of which radius
> ensures uniformity of film thickness within 10 percent of the value at that
> certain location. For example, a planarization length of 5 mm means all features
> (high and low) within 5 mm of any location within a chip are planarized with
> film thickness variation within 10 percent.
>
> Analytical expressions for step height evolution assume that the polishing pad
> deforms like a plate on an elastic foundation whose stiffness is proportional to
> the local pattern density. A higher pad stiffness gives better within-die
> uniformity.

Used for `planarization-length` and `copper-dishing`, cited as
`mrs-density-stepheight` and `ieee-dishing-model`.

---

## 6. Consumables and defects

**Query:** pad conditioning diamond disk asperity regeneration glazing removal rate stability CMP
**Outcome:** hit

> Pad conditioning using a diamond disk is inevitable to attain a high material
> removal rate (MRR) and to ensure the stability of the process.
>
> The pad surface is conditioned by the protruded diamond abrasives to regenerate
> pad pores and asperities as the conditioner rotates and sweeps back and forth
> from the pad centre to the pad periphery.
>
> During polishing, the reaction product gradually accumulates in holes and
> grooves in the pad surface, leading to "glazing" of the pad. Consequently, the
> wafer removal rate decreases because slurry can no longer be distributed
> uniformly on the pad surface. A diamond pad conditioner is employed either in
> situ or ex situ dressing to regenerate the asperity structure of the pad.
>
> If dressing stability is the major concern, the use of "blocky" diamond grit is
> recommended because it provided the most stable wafer removal rate over a
> conditioning time of up to 20 h.

Used for `pad-conditioning` and `pad-asperity-contact`, cited as
`sd-diamond-disc-conditioning` and `springer-diamond-shape`.

**Query:** tungsten CMP slurry chemistry ferric nitrate hydrogen peroxide passivation Kaufman model
**Outcome:** hit

> The CMP mechanism of W films was first proposed by Kaufman et al., which
> involves the removal of the W film by consecutive processes of passivation and
> abrasion action. Mechanical action to continually disrupt a surface passivating
> film on W, and chemical action to remove W, appear to be requirements for
> workability of the process.
>
> The slurry containing ferric nitrate induced a more dense oxide layer on
> tungsten surface while other compositions induced a porous oxide layer. H2O2 has
> been widely used as an oxidizer for commercial W CMP slurries due to its low
> cost and powerful oxidizing capability.
>
> When an oxidizing agent and a catalyst are used in combination, there is a
> strong synergistic effect that results in tungsten rates on the order of 5000
> A/min and greater, with the addition of catalytic amounts of ferric nitrate to
> hydrogen peroxide resulting in greater than one order of magnitude increase in
> tungsten rates.

Used for `tungsten-slurry-oxidizer`, cited as `sd-w-cmp-oxidants`. Kaufman's own
paper was not located and is an uncited lead.

**Query:** STI oxide CMP ceria slurry selectivity nitride stop layer high selectivity mechanism
**Outcome:** hit

> Ceria slurries are widely used in the shallow trench isolation (STI) CMP process
> due to their high selectivity in actively removing overburden SiO2 while
> stopping at the nitride layer.
>
> Material removal from the surface of oxide is attributed to the temporary
> attachment of ceria to the oxide surface due to the change in ceria surface
> charge characteristics at different pH conditions. Ceria polishes surfaces in
> lumped form through strong Ce-O-Si bonding.
>
> Certain amino acids such as l-proline and l-glutamic acid enhance the
> selectivity by suppressing the nitride removal rate. There is more absorbed
> additive on Si3N4 films than on SiO2 film.
>
> The purity of the abrasive and its crystal structure appear to play a
> significant role in determining the selectivity.

Used for `sti-ceria-slurry`, cited as `iop-sti-cmp-review` and
`sd-sti-selectivity`.

**Query:** copper CMP dishing erosion oxide loss pattern density overpolish barrier step
**Outcome:** hit

> Copper dishing is strongly feature size dependent, but rather insensitive to
> pattern density. Oxide erosion, on the other hand, is strongly pattern density
> dependent, but feature size independent.
>
> Varying feature density and the different mechanical properties of the metal and
> dielectric are the leading causes of polishing erosion.
>
> A multistep polishing process offers appreciable improvement over a single step
> process in dishing and erosion performance. Over polishing is main cause of all
> the CMP effects.
>
> At the barrier CMP stage, three materials are being simultaneously polished:
> residual copper, the TaN/Ta (or Co, Ru) barrier/liner, and the ILD oxide.

Used for `copper-dishing` and `oxide-erosion`, cited as `mit-boning-cu-damascene`.

**Query:** post-CMP PVA brush scrub megasonic clean particle removal chemistry mechanism
**Outcome:** hit

> In post-chemical mechanical polishing cleaning, polyvinyl acetal (PVA) brush
> scrubbing is considered the most effective way to remove the abrasive particles
> remaining on the wafer surface after the CMP process.
>
> Brush cleaning is an effective PCMP cleaning technique, and in an optimum mode, a
> contact between the particle and the brush is essential to the removal of
> submicron size particles from the wafer surface.
>
> CMP in-situ cleaning module normally consists of megasonic and brush scrubber
> processes. Megasonic (non-contact) cleaning uses high-frequency acoustic pressure
> waves to remove particles from the wafer surface.
>
> Effective particle removal was a second-order kinetic process with a
> concentration dependency (i.e. above and below the critical micelle
> concentration (CMC)) emerging as a key driver for the defect removal rate.

Used for `pva-brush-scrubber` and `megasonic-clean`, cited as
`entegris-pva-brush` and `rg-particle-adhesion`.

---

## 7. Head and membrane patents

**Query:** Applied Materials patent Zuniga carrier head flexible membrane multiple chambers independently pressurizable CMP
**Outcome:** hit

> Steven M. Zuniga is an inventor on multiple carrier head patents for chemical
> mechanical polishing.
>
> Some carrier heads include multiple chambers behind the flexible membrane, with
> each chamber able to be independently pressurized to cause the membrane to
> expand outwardly and apply different loads to different zones of the substrate.
>
> A carrier head includes a housing, base assembly, gimbal mechanism, loading
> chamber, retaining ring assembly with a first flexible membrane, a carrier ring,
> and a substrate backing assembly which includes a second flexible membrane that
> defines a plurality of pressurizable chambers.
>
> In some membrane designs, the pressure distribution can be non-uniform at the
> transition between different zones, potentially resulting in a pressure spike at
> the boundary between zones that can produce unintended non-uniformities in the
> polishing profile.

**Query:** Applied Materials patent retaining ring carrier head loading independent of wafer pressure CMP
**Outcome:** hit

> US6540594B2 - This carrier head provides independently controllable loads to the
> substrate and the retaining ring. The load on retaining ring is equal to the
> pressure in chamber 290 subtracted from the pressure in chamber 200.
>
> EP1066924A2 - The carrier head has a base, a flexible membrane extending beneath
> the base to define a pressurizable chamber, an edge load ring and a retaining
> ring.

Used for `carrier-head`, `carrier-membrane`, `retaining-ring`,
`zone-pressure-control`, cited as `pat-us6244942`, `pat-us6450868`,
`pat-us6540594`.

**Caution, and this is the important one.** None of these patents mentions the
Mirra by name in anything reached here. They are Applied Materials carrier head
patents from the right era, which is not the same as documentation of the shipped
machine. Every claim taken from them is written as general carrier head
behaviour, and the nodes say the specific construction on this platform is not
documented. Also, the `spec` and `claims` qualifiers used on these citations were
assigned from the summary wording, not from reading the patent parts. Verify
which part each claim actually comes from before trusting the qualifier.

---

## 8. The search that came back empty

**Query:** Mirra CMP 150mm configuration difference 200mm platen size retrofit polisher
**Outcome:** empty

The search returned dealer and refurbisher pages only. Nothing states what
changes between the 150 mm and 200 mm configurations. The one usable line was:

> The Applied Mirra CMP provides production-proven, high performance 150mm and
> 200mm planarization solutions for Silicon, shallow trench isolation (STI),
> oxide, polysilicon, tungsten and copper damascene applications.

which is cited as `entrepix-mirra` for the application list only.

One empty search is not a dead end. Re-run it with different phrasing before
recording it as one.

---

## 9. Leads found and not used

None of these is cited anywhere. They are worth a session's attention.

- Birang et al. 1998, "Process Control and Monitoring with Laser Interferometry
  Based Endpoint Detection in Chemical Mechanical Planarization". Would be a real
  source for the optical endpoint method.
- Kaufman et al., the original tungsten passivation and abrasion paper.
- eBay listing 0010-24500 "Mirra Titan II Profiler 200mm CMP polisher HEAD" and
  semigroup PDF 0010-77533 "200mm MIRRA Titan 1 HEAD". Tier 5, but part numbers
  and the Titan I and Titan II naming are checkable elsewhere.
- "Mirra 3400" as a dealer model designation.
- nccavs-usergroups.avs.org CMP User Group presentations, several years available
  as free PDFs. `nccavs-feeney-2012` is cited but was not read.
- US6886387 "Brush pressure calibration apparatus and method", assignee
  unconfirmed, which appears to describe the Mirra Mesa brush cleaner.

# Model Assumptions

## Purpose of this file
This file defines the simulation assumptions so future edits stay consistent with the project.

## Current simulation scope
The current app compares OLD versus NEW process structure using a simplified discrete-event simulation.

It is intended to estimate:
- throughput
- cycle time
- WIP
- queue waits
- utilization

It is not yet a full-factory model.

## Entity definition
Primary entity: rack

Important note:
- racks can carry different numbers of parts depending on part size
- current simulation primarily tracks racks, not individual parts
- future versions may optionally add part counts or rack-size classes

## Arrival behavior
Real system behavior:
- racks arrive in batches from upstream operations
- batch sizes depend on upstream production

Modeling guidance:
- deterministic single-rack arrivals should not be treated as the most realistic default anymore
- future versions should support batch arrivals as a first-class option
- a reasonable calibration target is about 20–30 racks per shift and 2 shifts per day

## Processing-time behavior
Stakeholder-based current estimates:
- coat 1: about 5–10 minutes
- flash/tack 1: about 15 minutes
- coat 2: about 5–10 minutes
- flash/tack 2: about 15 minutes
- bake: currently modeled around 70 minutes
- cool/removal: about 5 minutes
- move between paint and bake in NEW: currently modeled as a short delay, often around 5 minutes

Modeling guidance:
- fixed times are acceptable for simple mode
- a more realistic mode should allow time ranges or distributions, especially for coat times

## Capacity assumptions

### OLD process
- 6 combined chambers
- a rack occupies one combined chamber for the full duration:
  coat1 + flash1 + coat2 + flash2 + bake + cool

### NEW process
- 4 paint booths
- 6 bake-only chambers
- paint booth handles:
  coat1 + flash1 + coat2 + flash2
- then move delay
- then bake chamber handles:
  bake + cool

### Booth rack capacity
Real-world note:
- typically 2 paint racks can fit in one booth

Modeling guidance:
- future versions should support 2 racks per booth in the NEW process
- old process capacity should be reviewed carefully depending on whether each combined chamber also effectively handles multiple racks at once in reality

## Labor assumptions
Real-world note:
- 3 operators per shift
- each operator uses 2 booths

Current model:
- labor is not explicitly modeled

Modeling guidance:
- future versions should add optional labor constraints
- one simple approach is limiting simultaneously active booths based on operator availability

## Setup / cleaning / changeover assumptions
Real-world note:
- parts cleaning before paint: about 20–30 minutes depending on batch size
- paint mixing: about 10 minutes
- paint gun cleaning/changeover: about 20 minutes

Current model:
- these times are not explicitly modeled

Modeling guidance:
- future versions should support optional setup/changeover logic
- these may be modeled as pre-paint delays, batch setup times, or changeover penalties

## Downtime assumptions
Real-world note:
- weekly routine maintenance causes a few hours of booth downtime

Current model:
- no downtime modeled

Modeling guidance:
- future versions should support optional scheduled downtime

## Rework / quality assumptions
Real-world note:
- the major real bottleneck is the rework loop after topcoat:
  paint -> polish -> repair attempt -> PP2 -> repaint if needed

Current model:
- no rework, no polish, no PP2, no defect probability

Modeling guidance:
- this is the highest-priority realism improvement
- future versions should support:
  - defect probability
  - polish/repair stage
  - return loop to repaint
  - rework counters

## Queueing assumptions
Current model generally assumes:
- FIFO queues
- identical servers within each resource pool
- no priority logic
- no batching rules beyond what may be added for arrivals

## Metrics currently expected
The app should continue to produce:
- total completed within simulation window
- throughput
- mean cycle time
- 95th percentile cycle time
- average WIP
- queue wait metrics
- resource utilization

## Recommended modeling modes
To keep the app useful, support these modes when possible:

### Simple mode
- deterministic times
- simple arrivals
- no downtime
- no labor limits
- no rework

### Improved realism mode
- batch arrivals
- variable coat times
- 2 racks per booth
- optional labor limits
- optional downtime
- optional rework loop

This split helps preserve explainability while improving realism.

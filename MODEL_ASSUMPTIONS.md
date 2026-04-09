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
- scrap and rework outcomes

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
- the current app models arrivals as fixed-interval batches across the simulation window
- each batch releases the selected number of racks at the same timestamp
- setting batch size to 1 recreates the simple one-rack-at-a-time arrival pattern
- a reasonable calibration target is about 20-30 racks per shift and 2 shifts per day

## Processing-time behavior
Stakeholder-based current estimates:
- coat 1: about 5-10 minutes
- flash/tack 1: about 15 minutes
- coat 2: about 5-10 minutes
- flash/tack 2: about 15 minutes
- bake: currently modeled around 70 minutes
- cool/removal: about 5 minutes
- move between paint and bake in NEW: currently modeled as a short delay, often around 5 minutes

Modeling guidance:
- the current app supports a deterministic coat-time mode and a variable coat-time mode
- in variable mode, each coat is sampled independently from a uniform distribution between user-selected `coat_min` and `coat_max`
- flash time remains fixed
- fixed times are still available for simple mode

## Capacity assumptions

### OLD process
- 6 combined chambers
- each combined chamber is currently modeled with capacity for 2 simultaneous racks
- each rack occupies one of those chamber positions for the full duration:
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
- the current app models each NEW paint booth with capacity for 2 simultaneous racks
- booth capacity is represented as added parallel paint capacity while keeping FIFO queue logic
- the current app also models each OLD combined chamber with capacity for 2 simultaneous racks

## Rework / quality assumptions
Real-world note:
- the major real bottleneck is the rework loop after topcoat:
  paint -> polish -> repair attempt -> PP2 -> repaint if needed

Current model:
- each system has its own initial scrap rate
- each system has its own rework success rate
- if a rack fails initial processing, it enters a delay-only polish step and then returns through the full paint/bake process
- each failed rework cycle can loop again until the selected maximum rework-attempt limit is reached
- if a rack still fails after the allowed rework attempts, it becomes permanent scrap
- rework consumes the same OLD or NEW paint/bake resources as a normal rack

Modeling guidance:
- this is still a simplified representation of the real paint -> polish -> PP2 -> repaint loop
- polish is currently modeled as time delay only, not a separate constrained resource
- scrap and rework results should be interpreted as scenario-comparison outputs rather than exact production forecasts

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
- parts cleaning before paint: about 20-30 minutes depending on batch size
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

## Queueing assumptions
Current model generally assumes:
- FIFO queues
- identical servers within each resource pool
- no priority logic
- no batching rules beyond the scheduled arrival batches

## Metrics currently expected
The app should continue to produce:
- total completed within simulation window
- throughput
- mean cycle time
- 95th percentile cycle time
- average WIP
- queue wait metrics
- resource utilization
- final good completed racks
- total scrapped racks
- total reworked racks
- rework percentage

## Recommended modeling modes
To keep the app useful, support these modes when possible:

### Simple mode
- deterministic times
- batch size = 1 if a simple arrival pattern is preferred
- scrap and rework rates can be set to 0 if rework is not being studied
- no downtime
- no labor limits

### Improved realism mode
- batch arrivals
- variable coat times
- 2 racks per booth
- polish-triggered rework loops
- optional labor limits
- optional downtime

This split helps preserve explainability while improving realism.

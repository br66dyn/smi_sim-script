# Project Context

## Organization
SMI Composites

## Project Type
Senior mechanical engineering capstone project focused on modeling and comparing SMI's current paint-line process versus a proposed improved process.

## Main objective
Build a simulation that compares the OLD process to the NEW process and helps estimate performance differences such as throughput, cycle time, utilization, queueing, and work-in-progress.

## Why this model exists
The model is intended to support capstone analysis and communication. It should be useful for:
- understanding major bottlenecks
- comparing current-state versus future-state capacity
- testing what-if scenarios
- showing the likely impact of process changes in a simple and explainable way

## Current-state understanding from stakeholder feedback

### Arrival behavior
Racks do not arrive in a perfectly steady flow. They typically arrive in batches from upstream operations. Batch quantity depends heavily on upstream production output.

### Daily/shift volume
SMI processes roughly 20–30 paint racks per shift, with 2 shifts per day.
This implies a rough daily volume of about 40–60 racks per day under normal operation.

### Painting time
For a rack or booth load:
- first coat takes roughly 5–10 minutes
- tack/flash time is about 15 minutes
- second coat takes roughly 5–10 minutes

### Booth loading
Typically, 2 paint racks can fit in one booth at the same time.

### Rack capacity
Rack capacity depends on part size:
- large-part racks typically hold about 4–8 parts
- small-part racks can hold up to about 20 parts

### Cooling after bake
Racks are often removed from the booths within about 5 minutes after the bake cycle ends.

### Operators
Currently there are 3 operators per shift, and each operator uses 2 booths.
This implies the current labor arrangement is aligned with operating up to 6 booths/chambers in the current process.

### Setup / cleaning / changeover
Additional preparation and changeover activities exist in the real process:
- cleaning parts to prepare for paint takes roughly 20–30 minutes depending on batch size
- mixing paint takes roughly 10 minutes
- cleaning the paint gun and preparing for a different paint takes roughly 20 minutes

### Downtime / maintenance
About once per week, booths experience routine maintenance downtime.
Typical downtime includes:
- booth cleaning
- filter changes
- a few hours out of service

## Current bottleneck understanding
The largest operational bottleneck is not simply the paint or bake step. The most problematic bottleneck is the rework loop involving:
1. final topcoat applied
2. parts go to polish
3. polish attempts repair if there are defects
4. parts that cannot be repaired go to PP2 (paint prep 2)
5. topcoat is sanded away
6. parts are repainted

This paint → polish → PP2 → repaint loop is currently the most problematic bottleneck in the real system.

## Important implication for the simulation
The current simulation is still a simplification. It mainly captures paint/bake capacity comparison. It does not yet fully represent:
- polish
- PP2
- defect probability
- rework loops
- setup/cleaning/changeover
- weekly downtime
- labor constraints
- part-size mix

These should be considered future improvements rather than ignored realities.

## Current OLD vs NEW framing

### OLD process
The OLD process uses 6 combined chambers. A rack occupies one chamber for the full process sequence.

### NEW process
The NEW process separates paint and bake resources:
- 4 paint booths
- 6 bake-only chambers

The NEW process is intended to decouple paint/flash from bake/cool, improving flexibility and capacity use.

## Modeling philosophy
The user prefers a model that is:
- simple enough to understand and present
- editable
- robust
- gradually improvable

The user does not want a fragile or overly complex simulation that becomes hard to explain in a capstone setting.

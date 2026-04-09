# Project Context

## Capstone partner
SMI Composites

## Objective
Compare the old finishing process vs. a proposed new process using a simple, editable simulation.

## Why this simulation exists
The project needs a decision-support tool for comparing throughput, utilization, WIP, and queueing behavior between current-state and future-state process designs.

## Current model scope
- Entity = rack
- Deterministic arrivals
- Deterministic process times
- Simple DES, not a full factory digital twin

## Old process
- 6 combined chambers
- Each rack occupies one chamber for the full process:
  coat1 + flash1 + coat2 + flash2 + bake + cool

## New process
- 4 paint booths
- 6 bake-only chambers
- Paint/flash occur in paint booths
- Rack then moves to bake-only chamber
- Move time is modeled as delay-only

## Why simplifications were chosen
The user prefers simplicity and robustness over high complexity because the model needs to be understandable, editable, and usable for a senior capstone presentation.

## Known future improvements
- stochastic arrivals
- stochastic service times
- labor constraints
- downtime
- shift schedules
- queue length over time
- scenario presets

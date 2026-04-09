# Version 2 Roadmap

## Objective
Improve realism and usefulness of the SMI simulation without making the app fragile or overly complicated.

## Highest-priority improvements

### 1. Add batch arrivals
Reason:
Real racks arrive in batches from upstream operations, not in perfect one-at-a-time steady flow.

Target:
- allow user to choose batch size
- allow user to choose batch interval
- preserve simple deterministic mode if useful

### 2. Add variable coat times
Reason:
Actual coat application is roughly 5–10 minutes, not a single exact value.

Target:
- allow user to choose fixed times or range/distribution-based times
- start simple if needed (uniform or triangular)

### 3. Add 2-racks-per-booth logic
Reason:
Typically 2 paint racks fit in one booth, so single-rack-per-booth logic underestimates paint capacity.

Target:
- allow booth rack capacity to be set
- ensure queueing logic still works cleanly

### 4. Add optional labor constraints
Reason:
There are 3 operators per shift and each operator uses 2 booths.

Target:
- allow optional labor toggle
- tie active booth capacity to operator availability

### 5. Add setup / cleaning / changeover logic
Reason:
Real process includes:
- parts cleaning (20–30 min)
- paint mixing (~10 min)
- paint gun cleaning / color or coating changeover (~20 min)

Target:
- start with optional batch setup delays
- avoid overcomplicating the first implementation

### 6. Add scheduled downtime
Reason:
Booths go down weekly for routine maintenance.

Target:
- allow optional scheduled downtime input
- model a few hours of outage once per week or at a defined interval

### 7. Add rework loop
Reason:
The paint -> polish -> PP2 -> repaint loop is the largest real bottleneck and the most important missing realism feature.

Target:
- add optional defect probability
- add polish/repair stage
- add PP2/repaint loop
- track rework counts and rework burden

## Medium-priority improvements

### 8. Add queue-length-over-time plot
Useful for identifying where congestion builds.

### 9. Add scenario presets
Examples:
- current estimate
- optimistic new process
- stress case
- high rework case

### 10. Add export features
Allow export of:
- summary table
- scenario inputs
- selected metrics

## Constraints
- Keep Streamlit Cloud compatibility
- Avoid unnecessary heavy dependencies
- Preserve the current outputs unless intentionally replacing them
- Keep the code readable for a senior capstone project
- Maintain a simple baseline mode for presentation purposes

## Suggested implementation order
1. batch arrivals
2. variable coat times
3. 2-racks-per-booth logic
4. labor constraints
5. setup/changeover
6. downtime
7. rework loop
8. additional plots and export features

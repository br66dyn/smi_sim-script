# Version 2 Roadmap

## Objective
Improve realism and usefulness of the SMI simulation without making the app fragile or overly complicated.

## Highest-priority improvements

### Completed in current version

#### 1. Add batch arrivals
Reason:
Real racks arrive in batches from upstream operations, not in perfect one-at-a-time steady flow.

Implemented:
- user can choose batch size
- user can choose batch interval
- simple behavior is still available by setting batch size to 1

#### 2. Add variable coat times
Reason:
Actual coat application is roughly 5-10 minutes, not a single exact value.

Implemented:
- user can choose deterministic or variable coat timing
- variable mode uses a uniform range with user inputs for `coat_min` and `coat_max`

#### 3. Add 2-racks-per-booth logic
Reason:
Typically 2 paint racks fit in one booth, so single-rack-per-booth logic underestimates paint capacity.

Implemented:
- NEW paint booths now model capacity for 2 simultaneous racks
- FIFO queueing logic is preserved

### Next highest-priority improvements

#### 4. Add optional labor constraints
Reason:
There are 3 operators per shift and each operator uses 2 booths.

Target:
- allow optional labor toggle
- tie active booth capacity to operator availability

#### 5. Add setup / cleaning / changeover logic
Reason:
Real process includes:
- parts cleaning (20-30 min)
- paint mixing (~10 min)
- paint gun cleaning / color or coating changeover (~20 min)

Target:
- start with optional batch setup delays
- avoid overcomplicating the first implementation

#### 6. Add scheduled downtime
Reason:
Booths go down weekly for routine maintenance.

Target:
- allow optional scheduled downtime input
- model a few hours of outage once per week or at a defined interval

#### 7. Add rework loop
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

## Suggested implementation order from here
1. labor constraints
2. setup/changeover
3. downtime
4. rework loop
5. additional plots and export features

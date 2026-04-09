# app.py - Streamlit DES App: SMI OLD vs NEW
# Run locally:
#   pip install streamlit matplotlib pandas
#   streamlit run app.py
#
# This is a single-file, browser-based interactive app with sliders + live-updating outputs.

import heapq
import math
import random
from dataclasses import dataclass
from typing import Dict, List, Tuple

import matplotlib.pyplot as plt
import pandas as pd
import streamlit as st


# ============================== CORE DES (pure functions) ==============================

RNG_SEED = 42
OLD_COMBINED_CHAMBER_CAPACITY = 2
NEW_PAINT_BOOTH_CAPACITY = 2


@dataclass
class SimResults:
    name: str
    arrivals: List[float]
    completion_times: List[float]
    cycle_times: List[float]

    wait_combined: List[float]  # OLD
    wait_paint: List[float]  # NEW
    wait_bake: List[float]  # NEW

    util_combined: float  # OLD
    util_paint: float  # NEW
    util_bake: float  # NEW

    avg_wip: float
    scrap_times: List[float]
    total_reworked: int


def batch_arrivals(window_minutes: float, batch_size: int, batch_interval: float) -> List[float]:
    # Batches arrive across the full simulation window at fixed intervals.
    # Every rack in a batch is released at the same timestamp to represent upstream batch flow.
    arrivals: List[float] = []
    n_batches = int(math.floor(window_minutes / batch_interval)) + 1

    for i in range(n_batches):
        batch_time = i * batch_interval
        arrivals.extend([batch_time] * batch_size)

    return arrivals


def coat_duration(
    time_mode: str,
    deterministic_time: float,
    coat_min: float,
    coat_max: float,
    rng: random.Random,
) -> float:
    if time_mode == "Variable":
        return rng.uniform(coat_min, coat_max)
    return deterministic_time


def schedule_on_parallel_resource(arrival_time: float, service_time: float, next_free: List[float]) -> Tuple[float, float]:
    slot_index = min(range(len(next_free)), key=lambda k: next_free[k])
    start_time = max(arrival_time, next_free[slot_index])
    end_time = start_time + service_time
    next_free[slot_index] = end_time
    return start_time, end_time


def _sum_busy_within_window(starts: List[float], ends: List[float], window_T: float) -> float:
    busy = 0.0
    for s, e in zip(starts, ends):
        a = max(0.0, s)
        b = min(window_T, e)
        if b > a:
            busy += b - a
    return busy


def _time_weighted_wip(arrivals: List[float], departures: List[float], window_T: float) -> float:
    # Time-average WIP over [0, window_T] via event integration.
    events: List[Tuple[float, int]] = []
    for t in arrivals:
        if t <= window_T:
            events.append((t, +1))
    for t in departures:
        if t <= window_T:
            events.append((t, -1))

    if not events:
        return 0.0

    # At identical times: arrivals before departures (+1 then -1)
    events.sort(key=lambda x: (x[0], -x[1]))

    wip = 0
    last_t = 0.0
    area = 0.0

    for t, delta in events:
        if t > window_T:
            break
        area += wip * (t - last_t)
        wip += delta
        last_t = t

    area += wip * (window_T - last_t)
    return area / window_T


def percentile(data: List[float], p: float) -> float:
    if not data:
        return float("nan")
    d = sorted(data)
    k = (len(d) - 1) * (p / 100.0)
    f = math.floor(k)
    c = math.ceil(k)
    if f == c:
        return d[int(k)]
    return d[f] + (k - f) * (d[c] - d[f])


def process_rework_outcome(
    process_end: float,
    rack_id: int,
    rework_attempt: int,
    initial_arrivals: List[float],
    polish_time: float,
    max_rework_attempts: int,
    rework_success_rate: float,
    rng: random.Random,
    pending_racks: List[Tuple[float, int, int]],
    completion_times: List[float],
    cycle_times: List[float],
    scrap_times: List[float],
    final_departures: List[float],
) -> Tuple[int, bool]:
    if rng.random() < rework_success_rate:
        completion_times.append(process_end)
        cycle_times.append(process_end - initial_arrivals[rack_id])
        final_departures[rack_id] = process_end
        return 0, True

    if rework_attempt < max_rework_attempts:
        next_attempt = rework_attempt + 1
        heapq.heappush(pending_racks, (process_end + polish_time, rack_id, next_attempt))
        return 1, False

    scrap_times.append(process_end)
    final_departures[rack_id] = process_end
    return 0, False


def simulate_old(
    sim_hours: float,
    batch_size: int,
    batch_interval: float,
    n_combined: int,
    coat1: float,
    flash1: float,
    coat2: float,
    flash2: float,
    bake: float,
    cool: float,
    paint_time_mode: str,
    coat_min: float,
    coat_max: float,
    scrap_rate: float,
    rework_success_rate: float,
    polish_time: float,
    max_rework_attempts: int,
) -> SimResults:
    T = sim_hours * 60.0
    initial_arrivals = batch_arrivals(T, batch_size, batch_interval)
    rng = random.Random(RNG_SEED)

    combined_capacity = n_combined * OLD_COMBINED_CHAMBER_CAPACITY
    next_free = [0.0] * combined_capacity

    pending_racks = [(arrival, rack_id, 0) for rack_id, arrival in enumerate(initial_arrivals)]
    heapq.heapify(pending_racks)

    starts, ends = [], []
    waits, completion_times, cycle_times, scrap_times = [], [], [], []
    final_departures = [0.0] * len(initial_arrivals)
    total_reworked = 0

    while pending_racks:
        arrival_time, rack_id, rework_attempt = heapq.heappop(pending_racks)

        rack_coat1 = coat_duration(paint_time_mode, coat1, coat_min, coat_max, rng)
        rack_coat2 = coat_duration(paint_time_mode, coat2, coat_min, coat_max, rng)
        service_time = rack_coat1 + flash1 + rack_coat2 + flash2 + bake + cool

        start_time, end_time = schedule_on_parallel_resource(arrival_time, service_time, next_free)

        starts.append(start_time)
        ends.append(end_time)
        waits.append(start_time - arrival_time)

        if rework_attempt == 0:
            if rng.random() < scrap_rate:
                if max_rework_attempts > 0:
                    total_reworked += 1
                    heapq.heappush(pending_racks, (end_time + polish_time, rack_id, 1))
                else:
                    scrap_times.append(end_time)
                    final_departures[rack_id] = end_time
            else:
                completion_times.append(end_time)
                cycle_times.append(end_time - initial_arrivals[rack_id])
                final_departures[rack_id] = end_time
        else:
            added_rework, _ = process_rework_outcome(
                process_end=end_time,
                rack_id=rack_id,
                rework_attempt=rework_attempt,
                initial_arrivals=initial_arrivals,
                polish_time=polish_time,
                max_rework_attempts=max_rework_attempts,
                rework_success_rate=rework_success_rate,
                rng=rng,
                pending_racks=pending_racks,
                completion_times=completion_times,
                cycle_times=cycle_times,
                scrap_times=scrap_times,
                final_departures=final_departures,
            )
            total_reworked += added_rework

    busy_total = _sum_busy_within_window(starts, ends, T)
    util_combined = busy_total / (combined_capacity * T)
    avg_wip = _time_weighted_wip(initial_arrivals, final_departures, T)

    return SimResults(
        name="OLD",
        arrivals=initial_arrivals,
        completion_times=completion_times,
        cycle_times=cycle_times,
        wait_combined=waits,
        wait_paint=[],
        wait_bake=[],
        util_combined=util_combined,
        util_paint=float("nan"),
        util_bake=float("nan"),
        avg_wip=avg_wip,
        scrap_times=scrap_times,
        total_reworked=total_reworked,
    )


def simulate_new(
    sim_hours: float,
    batch_size: int,
    batch_interval: float,
    n_paint: int,
    n_bake: int,
    coat1: float,
    flash1: float,
    coat2: float,
    flash2: float,
    bake: float,
    cool: float,
    move: float,
    paint_time_mode: str,
    coat_min: float,
    coat_max: float,
    scrap_rate: float,
    rework_success_rate: float,
    polish_time: float,
    max_rework_attempts: int,
) -> SimResults:
    T = sim_hours * 60.0
    initial_arrivals = batch_arrivals(T, batch_size, batch_interval)
    rng = random.Random(RNG_SEED)

    paint_capacity = n_paint * NEW_PAINT_BOOTH_CAPACITY
    next_free_p = [0.0] * paint_capacity
    next_free_b = [0.0] * n_bake

    pending_racks = [(arrival, rack_id, 0) for rack_id, arrival in enumerate(initial_arrivals)]
    heapq.heapify(pending_racks)

    p_start, p_end, p_wait = [], [], []
    b_start, b_end, b_wait = [], [], []
    completion_times, cycle_times, scrap_times = [], [], []
    final_departures = [0.0] * len(initial_arrivals)
    total_reworked = 0

    while pending_racks:
        arrival_time, rack_id, rework_attempt = heapq.heappop(pending_racks)

        rack_coat1 = coat_duration(paint_time_mode, coat1, coat_min, coat_max, rng)
        rack_coat2 = coat_duration(paint_time_mode, coat2, coat_min, coat_max, rng)
        paint_service_time = rack_coat1 + flash1 + rack_coat2 + flash2
        bake_service_time = bake + cool

        paint_start, paint_end = schedule_on_parallel_resource(arrival_time, paint_service_time, next_free_p)
        bake_arrival = paint_end + move
        bake_start, bake_end = schedule_on_parallel_resource(bake_arrival, bake_service_time, next_free_b)

        p_start.append(paint_start)
        p_end.append(paint_end)
        p_wait.append(paint_start - arrival_time)

        b_start.append(bake_start)
        b_end.append(bake_end)
        b_wait.append(bake_start - bake_arrival)

        if rework_attempt == 0:
            if rng.random() < scrap_rate:
                if max_rework_attempts > 0:
                    total_reworked += 1
                    heapq.heappush(pending_racks, (bake_end + polish_time, rack_id, 1))
                else:
                    scrap_times.append(bake_end)
                    final_departures[rack_id] = bake_end
            else:
                completion_times.append(bake_end)
                cycle_times.append(bake_end - initial_arrivals[rack_id])
                final_departures[rack_id] = bake_end
        else:
            added_rework, _ = process_rework_outcome(
                process_end=bake_end,
                rack_id=rack_id,
                rework_attempt=rework_attempt,
                initial_arrivals=initial_arrivals,
                polish_time=polish_time,
                max_rework_attempts=max_rework_attempts,
                rework_success_rate=rework_success_rate,
                rng=rng,
                pending_racks=pending_racks,
                completion_times=completion_times,
                cycle_times=cycle_times,
                scrap_times=scrap_times,
                final_departures=final_departures,
            )
            total_reworked += added_rework

    busy_p = _sum_busy_within_window(p_start, p_end, T)
    busy_b = _sum_busy_within_window(b_start, b_end, T)

    util_paint = busy_p / (paint_capacity * T)
    util_bake = busy_b / (n_bake * T)
    avg_wip = _time_weighted_wip(initial_arrivals, final_departures, T)

    return SimResults(
        name="NEW",
        arrivals=initial_arrivals,
        completion_times=completion_times,
        cycle_times=cycle_times,
        wait_combined=[],
        wait_paint=p_wait,
        wait_bake=b_wait,
        util_combined=float("nan"),
        util_paint=util_paint,
        util_bake=util_bake,
        avg_wip=avg_wip,
        scrap_times=scrap_times,
        total_reworked=total_reworked,
    )


def build_summary_df(old: SimResults, new: SimResults, sim_hours: float) -> pd.DataFrame:
    T = sim_hours * 60.0

    def row(res: SimResults) -> Dict[str, float]:
        completed_within = sum(1 for t in res.completion_times if t <= T)
        throughput = completed_within / sim_hours
        mean_ct = sum(res.cycle_times) / len(res.cycle_times) if res.cycle_times else float("nan")
        p95_ct = percentile(res.cycle_times, 95)
        rework_pct = (res.total_reworked / len(res.arrivals) * 100.0) if res.arrivals else float("nan")
        return {
            "Total Completed (<=window)": float(completed_within),
            "Throughput (racks/hr)": throughput,
            "Mean Cycle Time (min)": mean_ct,
            "P95 Cycle Time (min)": p95_ct,
            "Avg WIP (0-window)": res.avg_wip,
            "Final Good Completed": float(len(res.completion_times)),
            "Total Scrapped": float(len(res.scrap_times)),
            "Total Reworked": float(res.total_reworked),
            "Rework % of Initial Racks": rework_pct,
        }

    df = pd.DataFrame({"OLD": row(old), "NEW": row(new)}).T

    df["Util Combined"] = [old.util_combined, float("nan")]
    df["Util Paint"] = [float("nan"), new.util_paint]
    df["Util Bake"] = [float("nan"), new.util_bake]

    df["Mean Wait Combined (min)"] = [sum(old.wait_combined) / len(old.wait_combined), float("nan")]
    df["Mean Wait Paint (min)"] = [float("nan"), sum(new.wait_paint) / len(new.wait_paint)]
    df["Mean Wait Bake (min)"] = [float("nan"), sum(new.wait_bake) / len(new.wait_bake)]

    return df


def step_xy(times: List[float]) -> Tuple[List[float], List[float]]:
    ts = sorted(times)
    x, y = [0.0], [0]
    count = 0
    for t in ts:
        count += 1
        x.extend([t, t])
        y.extend([count - 1, count])
    return x, y


def rework_percentage(res: SimResults) -> float:
    if not res.arrivals:
        return float("nan")
    return res.total_reworked / len(res.arrivals) * 100.0


# ============================== STREAMLIT UI ==============================

st.set_page_config(page_title="SMI DES: OLD vs NEW", layout="wide")

st.title("SMI Discrete-Event Simulation: OLD vs NEW")
st.caption(
    "Batch arrivals with selectable deterministic or variable coat times, plus polish-triggered rework loops. "
    "OLD uses combined chambers; NEW uses decoupled paint booths and bake-only chambers."
)

with st.sidebar:
    st.header("Simulation")
    sim_hours = st.slider("Simulation window (hours)", min_value=1, max_value=168, value=24, step=1)
    batch_size = st.slider("Batch size (racks per batch)", min_value=1, max_value=20, value=1, step=1)
    batch_interval = st.slider("Batch interval (minutes between batches)", min_value=1, max_value=240, value=30, step=1)
    st.caption("Set batch size to 1 to recover the original one-rack-at-a-time arrival pattern.")

    st.divider()
    st.header("Resources")
    n_combined = st.slider("OLD: # Combined chambers", min_value=1, max_value=20, value=6, step=1)
    n_paint = st.slider("NEW: # Paint booths", min_value=1, max_value=20, value=4, step=1)
    n_bake = st.slider("NEW: # Bake chambers", min_value=1, max_value=20, value=6, step=1)
    st.caption("OLD combined chambers and NEW paint booths are both modeled with capacity for 2 racks at once.")

    st.divider()
    st.header("Paint Application")
    paint_time_mode = st.selectbox("Coat time mode", options=["Deterministic", "Variable"], index=0)
    coat_min = st.number_input("coat_min", min_value=0.0, value=5.0, step=0.5)
    coat_max = st.number_input("coat_max", min_value=0.0, value=10.0, step=0.5)
    st.caption("Variable mode samples each coat uniformly between coat_min and coat_max.")

    st.divider()
    st.header("Rework")
    polish_time = st.slider("Polish time before rework (minutes)", min_value=0, max_value=240, value=20, step=1)
    max_rework_attempts = st.slider("Max rework attempts", min_value=0, max_value=10, value=1, step=1)

    st.subheader("OLD rework settings")
    old_scrap_rate = st.slider("OLD initial scrap rate (%)", min_value=0.0, max_value=100.0, value=10.0, step=1.0)
    old_rework_success_rate = st.slider("OLD rework success rate (%)", min_value=0.0, max_value=100.0, value=60.0, step=1.0)

    st.subheader("NEW rework settings")
    new_scrap_rate = st.slider("NEW initial scrap rate (%)", min_value=0.0, max_value=100.0, value=5.0, step=1.0)
    new_rework_success_rate = st.slider("NEW rework success rate (%)", min_value=0.0, max_value=100.0, value=75.0, step=1.0)

    st.divider()
    st.header("Times - OLD (minutes)")
    old_coat1 = st.number_input("OLD coat1", min_value=0.0, value=20.0, step=1.0)
    old_flash1 = st.number_input("OLD flash1", min_value=0.0, value=15.0, step=1.0)
    old_coat2 = st.number_input("OLD coat2", min_value=0.0, value=20.0, step=1.0)
    old_flash2 = st.number_input("OLD flash2", min_value=0.0, value=15.0, step=1.0)
    old_bake = st.number_input("OLD bake", min_value=0.0, value=70.0, step=1.0)
    old_cool = st.number_input("OLD cool", min_value=0.0, value=10.0, step=1.0)

    st.divider()
    st.header("Times - NEW (minutes)")
    new_coat1 = st.number_input("NEW coat1", min_value=0.0, value=10.0, step=1.0)
    new_flash1 = st.number_input("NEW flash1", min_value=0.0, value=15.0, step=1.0)
    new_coat2 = st.number_input("NEW coat2", min_value=0.0, value=10.0, step=1.0)
    new_flash2 = st.number_input("NEW flash2", min_value=0.0, value=15.0, step=1.0)
    new_bake = st.number_input("NEW bake", min_value=0.0, value=70.0, step=1.0)
    new_cool = st.number_input("NEW cool", min_value=0.0, value=10.0, step=1.0)
    new_move = st.number_input("NEW move (delay-only)", min_value=0.0, value=5.0, step=1.0)


if batch_interval <= 0:
    st.error("Batch interval must be > 0")
    st.stop()

if coat_max < coat_min:
    st.error("coat_max must be greater than or equal to coat_min")
    st.stop()


old = simulate_old(
    sim_hours=sim_hours,
    batch_size=int(batch_size),
    batch_interval=float(batch_interval),
    n_combined=int(n_combined),
    coat1=float(old_coat1),
    flash1=float(old_flash1),
    coat2=float(old_coat2),
    flash2=float(old_flash2),
    bake=float(old_bake),
    cool=float(old_cool),
    paint_time_mode=paint_time_mode,
    coat_min=float(coat_min),
    coat_max=float(coat_max),
    scrap_rate=float(old_scrap_rate) / 100.0,
    rework_success_rate=float(old_rework_success_rate) / 100.0,
    polish_time=float(polish_time),
    max_rework_attempts=int(max_rework_attempts),
)

new = simulate_new(
    sim_hours=sim_hours,
    batch_size=int(batch_size),
    batch_interval=float(batch_interval),
    n_paint=int(n_paint),
    n_bake=int(n_bake),
    coat1=float(new_coat1),
    flash1=float(new_flash1),
    coat2=float(new_coat2),
    flash2=float(new_flash2),
    bake=float(new_bake),
    cool=float(new_cool),
    move=float(new_move),
    paint_time_mode=paint_time_mode,
    coat_min=float(coat_min),
    coat_max=float(coat_max),
    scrap_rate=float(new_scrap_rate) / 100.0,
    rework_success_rate=float(new_rework_success_rate) / 100.0,
    polish_time=float(polish_time),
    max_rework_attempts=int(max_rework_attempts),
)

summary_df = build_summary_df(old, new, sim_hours)


# ============================== OUTPUTS ==============================

col1, col2 = st.columns([2, 1], gap="large")

with col1:
    st.subheader("Throughput Comparison")
    T = sim_hours * 60.0
    xo, yo = step_xy(old.completion_times)
    xn, yn = step_xy(new.completion_times)

    fig1 = plt.figure()
    plt.plot([t / 60.0 for t in xo], yo, label="OLD")
    plt.plot([t / 60.0 for t in xn], yn, label="NEW")
    plt.axvline(T / 60.0, linestyle="--", label="arrival window")
    plt.xlabel("Time (hours)")
    plt.ylabel("Cumulative good racks completed")
    plt.title("Cumulative Good Completions")
    plt.legend()
    plt.tight_layout()
    st.pyplot(fig1, clear_figure=True)

with col2:
    st.subheader("Utilization Dashboard")
    util_df = pd.DataFrame(
        {
            "Resource": ["OLD Combined", "NEW Paint", "NEW Bake"],
            "Utilization (%)": [old.util_combined * 100.0, new.util_paint * 100.0, new.util_bake * 100.0],
        }
    )

    fig2 = plt.figure()
    plt.bar(util_df["Resource"], util_df["Utilization (%)"])
    plt.ylim(0, 100)
    plt.ylabel("Utilization (%)")
    plt.title("Utilization (%)")
    plt.tight_layout()
    st.pyplot(fig2, clear_figure=True)

st.subheader("WIP & Queue Analysis")

qa_cols = st.columns(3)
qa_cols[0].metric("Avg WIP (OLD)", f"{old.avg_wip:.3f}")
qa_cols[1].metric("Avg WIP (NEW)", f"{new.avg_wip:.3f}")

old_mean_wait = sum(old.wait_combined) / len(old.wait_combined) if old.wait_combined else float("nan")
new_mean_wait_p = sum(new.wait_paint) / len(new.wait_paint) if new.wait_paint else float("nan")
new_mean_wait_b = sum(new.wait_bake) / len(new.wait_bake) if new.wait_bake else float("nan")

qa_cols[2].metric(
    "Mean Waits (min)",
    f"OLD {old_mean_wait:.2f} | NEW paint {new_mean_wait_p:.2f} | NEW bake {new_mean_wait_b:.2f}",
)

st.subheader("Rework Outcomes")
rework_cols = st.columns(4)
rework_cols[0].metric("Final Good Completed", f"OLD {len(old.completion_times)} | NEW {len(new.completion_times)}")
rework_cols[1].metric("Total Scrapped", f"OLD {len(old.scrap_times)} | NEW {len(new.scrap_times)}")
rework_cols[2].metric("Total Reworked", f"OLD {old.total_reworked} | NEW {new.total_reworked}")
rework_cols[3].metric("Rework %", f"OLD {rework_percentage(old):.1f}% | NEW {rework_percentage(new):.1f}%")

st.subheader("Summary Table")
st.dataframe(summary_df.style.format(precision=3), use_container_width=True)

with st.expander("Model assumptions (what this sim is and is NOT)"):
    st.markdown(
        """
- Batch arrivals occur at a fixed batch interval, and each batch releases the selected number of racks at once.
- Coat times can stay deterministic or vary uniformly between `coat_min` and `coat_max`; flash time stays fixed.
- A failed rack enters a delay-only polish step, then returns through the full OLD or NEW process as a rework rack.
- Each system has its own initial scrap rate and rework success rate.
- Rework attempts use the same paint and bake resources as normal racks, and racks are permanently scrapped when they fail after the selected rework-attempt limit.
- FIFO queues with identical parallel servers.
- OLD: each combined chamber provides capacity for 2 racks through the entire process (coat/flash/coat/flash/bake/cool).
- NEW: each paint booth provides capacity for 2 racks at once, then each rack moves after paint and waits for bake/cool separately.
- No labor constraints, no downtimes, no shift schedules.

If you want labor limits or downtime, the core DES can be extended.
"""
    )

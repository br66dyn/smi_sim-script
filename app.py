# app.py — Streamlit DES App: SMI OLD vs NEW
# Run locally:
#   pip install streamlit matplotlib pandas
#   streamlit run app.py
#
# This is a single-file, browser-based interactive app with sliders + live-updating outputs.

import math
from dataclasses import dataclass
from typing import Dict, List, Tuple

import matplotlib.pyplot as plt
import pandas as pd
import streamlit as st


# ============================== CORE DES (pure functions) ==============================

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


def deterministic_arrivals(T: float, IA: float) -> List[float]:
    # arrivals at 0, IA, 2IA, ... up to and including T
    n = int(math.floor(T / IA)) + 1
    return [i * IA for i in range(n)]


def _sum_busy_within_window(starts: List[float], ends: List[float], window_T: float) -> float:
    busy = 0.0
    for s, e in zip(starts, ends):
        a = max(0.0, s)
        b = min(window_T, e)
        if b > a:
            busy += (b - a)
    return busy


def _time_weighted_wip(arrivals: List[float], completions: List[float], window_T: float) -> float:
    # Time-average WIP over [0, window_T] via event integration.
    events: List[Tuple[float, int]] = []
    for t in arrivals:
        if t <= window_T:
            events.append((t, +1))
    for t in completions:
        if t <= window_T:
            events.append((t, -1))

    if not events:
        return 0.0

    # At identical times: arrivals before completions (+1 then -1)
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


def simulate_old(
    sim_hours: float,
    IA: float,
    n_combined: int,
    coat1: float,
    flash1: float,
    coat2: float,
    flash2: float,
    bake: float,
    cool: float,
) -> SimResults:
    T = sim_hours * 60.0

    S = coat1 + flash1 + coat2 + flash2 + bake + cool
    arrivals = deterministic_arrivals(T, IA)

    next_free = [0.0] * n_combined

    starts, ends, waits, cycles, completions = [], [], [], [], []

    for a in arrivals:
        j = min(range(n_combined), key=lambda k: next_free[k])
        start = max(a, next_free[j])
        end = start + S
        next_free[j] = end

        starts.append(start)
        ends.append(end)
        waits.append(start - a)
        cycles.append(end - a)
        completions.append(end)

    busy_total = _sum_busy_within_window(starts, ends, T)
    util_combined = busy_total / (n_combined * T)

    avg_wip = _time_weighted_wip(arrivals, completions, T)

    return SimResults(
        name="OLD",
        arrivals=arrivals,
        completion_times=completions,
        cycle_times=cycles,
        wait_combined=waits,
        wait_paint=[],
        wait_bake=[],
        util_combined=util_combined,
        util_paint=float("nan"),
        util_bake=float("nan"),
        avg_wip=avg_wip,
    )


def simulate_new(
    sim_hours: float,
    IA: float,
    n_paint: int,
    n_bake: int,
    coat1: float,
    flash1: float,
    coat2: float,
    flash2: float,
    bake: float,
    cool: float,
    move: float,
) -> SimResults:
    T = sim_hours * 60.0

    S_paint = coat1 + flash1 + coat2 + flash2
    S_bake = bake + cool

    arrivals = deterministic_arrivals(T, IA)

    # Stage A: paint booths
    next_free_p = [0.0] * n_paint
    p_start, p_end, p_wait = [], [], []

    for a in arrivals:
        j = min(range(n_paint), key=lambda k: next_free_p[k])
        start = max(a, next_free_p[j])
        end = start + S_paint
        next_free_p[j] = end

        p_start.append(start)
        p_end.append(end)
        p_wait.append(start - a)

    # Stage B: move delay
    bake_arrivals = [e + move for e in p_end]

    # Stage C: bake chambers
    next_free_b = [0.0] * n_bake
    b_start, b_end, b_wait = [], [], []

    for a2 in bake_arrivals:
        j = min(range(n_bake), key=lambda k: next_free_b[k])
        start = max(a2, next_free_b[j])
        end = start + S_bake
        next_free_b[j] = end

        b_start.append(start)
        b_end.append(end)
        b_wait.append(start - a2)

    completions = b_end
    cycles = [c - a for c, a in zip(completions, arrivals)]

    busy_p = _sum_busy_within_window(p_start, p_end, T)
    busy_b = _sum_busy_within_window(b_start, b_end, T)

    util_paint = busy_p / (n_paint * T)
    util_bake = busy_b / (n_bake * T)

    avg_wip = _time_weighted_wip(arrivals, completions, T)

    return SimResults(
        name="NEW",
        arrivals=arrivals,
        completion_times=completions,
        cycle_times=cycles,
        wait_combined=[],
        wait_paint=p_wait,
        wait_bake=b_wait,
        util_combined=float("nan"),
        util_paint=util_paint,
        util_bake=util_bake,
        avg_wip=avg_wip,
    )


def build_summary_df(old: SimResults, new: SimResults, sim_hours: float) -> pd.DataFrame:
    T = sim_hours * 60.0

    def row(res: SimResults) -> Dict[str, float]:
        completed_within = sum(1 for t in res.completion_times if t <= T)
        throughput = completed_within / sim_hours
        mean_ct = sum(res.cycle_times) / len(res.cycle_times) if res.cycle_times else float("nan")
        p95_ct = percentile(res.cycle_times, 95)
        return {
            "Total Completed (<=window)": float(completed_within),
            "Throughput (racks/hr)": throughput,
            "Mean Cycle Time (min)": mean_ct,
            "P95 Cycle Time (min)": p95_ct,
            "Avg WIP (0-window)": res.avg_wip,
        }

    df = pd.DataFrame({"OLD": row(old), "NEW": row(new)}).T

    # add utilizations + waits
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


# ============================== STREAMLIT UI ==============================

st.set_page_config(page_title="SMI DES: OLD vs NEW", layout="wide")

st.title("SMI Discrete-Event Simulation: OLD vs NEW")
st.caption(
    "Deterministic arrivals + deterministic processing times. "
    "OLD uses combined chambers; NEW uses decoupled paint booths and bake-only chambers."
)

with st.sidebar:
    st.header("Simulation")
    sim_hours = st.slider("Simulation window (hours)", min_value=1, max_value=168, value=24, step=1)
    IA = st.slider("Arrival interval IA (minutes)", min_value=1, max_value=240, value=30, step=1)

    st.divider()
    st.header("Resources")
    # You asked: new paint + bake editable. Keeping OLD editable too (useful for comparison).
    n_combined = st.slider("OLD: # Combined chambers", min_value=1, max_value=20, value=6, step=1)
    n_paint = st.slider("NEW: # Paint booths", min_value=1, max_value=20, value=4, step=1)
    n_bake = st.slider("NEW: # Bake chambers", min_value=1, max_value=20, value=6, step=1)

    st.divider()
    st.header("Times — OLD (minutes)")
    old_coat1 = st.number_input("OLD coat1", min_value=0.0, value=20.0, step=1.0)
    old_flash1 = st.number_input("OLD flash1", min_value=0.0, value=15.0, step=1.0)
    old_coat2 = st.number_input("OLD coat2", min_value=0.0, value=20.0, step=1.0)
    old_flash2 = st.number_input("OLD flash2", min_value=0.0, value=15.0, step=1.0)
    old_bake = st.number_input("OLD bake", min_value=0.0, value=70.0, step=1.0)
    old_cool = st.number_input("OLD cool", min_value=0.0, value=10.0, step=1.0)

    st.divider()
    st.header("Times — NEW (minutes)")
    new_coat1 = st.number_input("NEW coat1", min_value=0.0, value=10.0, step=1.0)
    new_flash1 = st.number_input("NEW flash1", min_value=0.0, value=15.0, step=1.0)
    new_coat2 = st.number_input("NEW coat2", min_value=0.0, value=10.0, step=1.0)
    new_flash2 = st.number_input("NEW flash2", min_value=0.0, value=15.0, step=1.0)
    new_bake = st.number_input("NEW bake", min_value=0.0, value=70.0, step=1.0)
    new_cool = st.number_input("NEW cool", min_value=0.0, value=10.0, step=1.0)
    new_move = st.number_input("NEW move (delay-only)", min_value=0.0, value=5.0, step=1.0)


# Guardrails
if IA <= 0:
    st.error("IA must be > 0")
    st.stop()

# Run simulations
old = simulate_old(
    sim_hours=sim_hours,
    IA=float(IA),
    n_combined=int(n_combined),
    coat1=float(old_coat1),
    flash1=float(old_flash1),
    coat2=float(old_coat2),
    flash2=float(old_flash2),
    bake=float(old_bake),
    cool=float(old_cool),
)

new = simulate_new(
    sim_hours=sim_hours,
    IA=float(IA),
    n_paint=int(n_paint),
    n_bake=int(n_bake),
    coat1=float(new_coat1),
    flash1=float(new_flash1),
    coat2=float(new_coat2),
    flash2=float(new_flash2),
    bake=float(new_bake),
    cool=float(new_cool),
    move=float(new_move),
)

summary_df = build_summary_df(old, new, sim_hours)


# ============================== OUTPUTS ==============================

col1, col2 = st.columns([2, 1], gap="large")

with col1:
    st.subheader("Throughput Comparison")
    # Matplotlib figure
    T = sim_hours * 60.0
    xo, yo = step_xy(old.completion_times)
    xn, yn = step_xy(new.completion_times)

    fig1 = plt.figure()
    plt.plot([t / 60.0 for t in xo], yo, label="OLD")
    plt.plot([t / 60.0 for t in xn], yn, label="NEW")
    plt.axvline(T / 60.0, linestyle="--", label="arrival window")
    plt.xlabel("Time (hours)")
    plt.ylabel("Cumulative racks completed")
    plt.title("Cumulative Completions")
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

qa_cols[2].metric("Mean Waits (min)", f"OLD {old_mean_wait:.2f} | NEW paint {new_mean_wait_p:.2f} | NEW bake {new_mean_wait_b:.2f}")

st.subheader("Summary Table")
st.dataframe(summary_df.style.format(precision=3), use_container_width=True)

with st.expander("Model assumptions (what this sim is and is NOT)"):
    st.markdown(
        """
- Deterministic arrivals (fixed IA) and deterministic step times.
- FIFO queues with identical parallel servers.
- OLD: a rack occupies one *combined* chamber for the entire process (coat/flash/coat/flash/bake/cool).
- NEW: rack occupies paint booth for coat/flash/coat/flash, then a delay-only move, then a bake chamber for bake/cool.
- No labor constraints, no downtimes, no scrap/rework, no shift schedules.

If you want variability (distributions), downtimes, or labor limits, the core DES can be extended.
"""
    )

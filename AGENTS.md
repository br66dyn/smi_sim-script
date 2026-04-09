# AGENTS.md

## Project
This repository contains a Streamlit-based discrete-event simulation (DES) for a senior capstone project with SMI Composites.

## Primary goal
Improve the simulation so it more accurately reflects the real paint-line operation while keeping the app understandable, editable, and stable for academic and stakeholder use.

## Required behavior
- Read `PROJECT_CONTEXT.md`, `MODEL_ASSUMPTIONS.md`, and `V2_ROADMAP.md` before making changes.
- Preserve the existing working Streamlit app unless explicitly asked to replace or refactor it.
- Prefer simple, readable Python over complex abstractions.
- Keep the app compatible with Streamlit Cloud.
- Avoid unnecessary dependencies.
- Preserve current outputs unless a change clearly improves them.
- If simulation logic changes, update `MODEL_ASSUMPTIONS.md`.
- If roadmap items are completed, update `V2_ROADMAP.md`.

## Coding preferences
- Keep functions small and easy to trace.
- Use clear variable names.
- Add comments where modeling assumptions matter.
- Do not overengineer.
- Do not silently remove existing functionality.

## Validation expectations
- The app should run without import errors.
- The app should still render key outputs: throughput, utilization, WIP/wait information, and summary table.
- Any new inputs should be exposed clearly in the UI.
- Deterministic/simple mode should remain available even if more realistic options are added.

## Context notes
This is a capstone decision-support model, not a full production digital twin. Accuracy should improve, but readability and explainability matter.

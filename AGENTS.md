# AGENTS.md

## Project
This repository contains a Streamlit discrete-event simulation for the SMI senior capstone project.

## Primary goal
Preserve the existing working app while adding Version 2 features safely.

## Rules
- Do not break the existing deterministic simulation.
- Keep the app compatible with Streamlit Cloud.
- Prefer simple, readable Python over complex abstractions.
- Avoid unnecessary dependencies.
- Keep all user-facing controls in the Streamlit sidebar unless there is a strong reason otherwise.
- Preserve existing outputs unless explicitly replacing them with better versions.
- Explain major modeling assumptions in comments and markdown files.
- If changing simulation logic, update MODEL_ASSUMPTIONS.md.
- If adding a feature, update V2_ROADMAP.md to reflect completion.

## Run instructions
- Install with: pip install -r requirements.txt
- Run with: streamlit run app.py

## Definition of done
- App runs without import errors.
- Existing charts still render.
- Existing metrics still compute.
- Any new feature has a visible UI and a brief explanation.

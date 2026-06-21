# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this is

A single-file Tkinter desktop app (`fun_times.py`) that tells you whether the tide will be high enough to swim at a given Auckland-area beach, for today, tomorrow, or the next 14 days. It also exports a detailed PDF report (hourly tide heights, sunrise/sunset, moon phase) for a chosen date range, useful for trip planning. It combines tide predictions from the NIWA Tides API with sunrise/sunset/moon-phase data from the `astral` library, and renders PDFs with `fpdf2`.

## Running the app

```bash
pip install requests pandas astral fpdf2
python3 fun_times.py
```

The app expects a conda environment (the repo's dev environment is a conda env named `tides`); activate it with `conda activate tides` before installing packages or running the script.

Requires a `.env` file (copy from `env.example`) with `NIWA_API_KEY=<key>` — get a key at https://api.niwa.co.nz/. `fun_times.py` loads `.env` itself via a hand-rolled parser (no `python-dotenv` dependency) and checks for required packages (`tkinter`, `requests`, `pandas`, `astral`, `fpdf2`) at startup with friendly install instructions if missing.

There is no test suite, linter, or build step in this repo.

## Architecture

Everything lives in `fun_times.py`, structured top-to-bottom as:

1. **Startup checks** — Python version and package availability checks before any real imports, so failures produce readable error messages instead of tracebacks.
2. **Data model** — `Beach` (lat/long/min good tide height) and `QueryType` (date range + NIWA query params) classes. `QueryType.query_niwa()` hits `https://api.niwa.co.nz/tides/data`.
3. **Beach data** — loaded from `beaches.csv` (columns: `beach,lat,long,good_height`) into a `beach_dict` at module load time. Adding a beach means adding a CSV row; no code change needed. The CSV currently has inconsistent spacing in some rows (leading spaces before lat/long on the last two lines) — be careful preserving exact formatting if editing it.
4. **Swim-time computation** (`swim_times()`) — the core logic:
   - Queries NIWA for tide heights over the requested date range.
   - Marks each timestamp as `high_enough_tide` if it exceeds the beach's `good_height`.
   - For each day, computes a time window to check based on the user's "Swim Time" selection (`All Day`, `Sneaky Morning Swim`, `After Work`), using real sunrise/sunset (via `get_sunrise_sunset()`/`astral`) combined with fixed fallback times in the `times` dict.
   - Finds contiguous "good tide" windows within that day's window and reports them (handles multiple disjoint windows per day, e.g. two high-tide periods).
5. **GUI** — built with Tkinter at the bottom of the file: beach/time dropdowns, a date entry + days spinbox for the detailed report, action buttons (today / tomorrow / next 2 weeks / clear / generate detailed report), and a scrollable text output. Platform-specific button styling differs between Mac (`highlightbackground`) and Windows/Linux (`bg`/`fg`) since Tkinter button theming isn't cross-platform consistent.
6. **Detailed PDF report** (`generate_detailed_report()`, called via `generate_report_callback()`) — queries NIWA the same way `swim_times()` does, then builds one `fpdf2` page per day (capped at 30 days) showing hourly tide heights from 05:00–22:00 (`get_hourly_tide_heights()`, using `Series.asof()` for nearest-prior-reading lookup), sunrise/sunset, and moon phase (`get_moon_phase()`, bucketing `astral.moon.phase()` into 8 named phases). Unlike the swim-check flow (which writes to the `message` Text widget), this flow uses `tkinter.filedialog.asksaveasfilename()` for the save location and `tkinter.messagebox` for success/error feedback, since it's a one-shot file export rather than a running log.

All times are converted to/displayed in `Pacific/Auckland` regardless of host machine timezone.

## Other directories

- `archive/` — older/superseded versions of the script and notebooks (`tides.py`, `fun_times.py`, notebooks). Not used by the current app; check here only if comparing historical behavior.
- `.ipynb_checkpoints/` — Jupyter autosave artifacts, not source of truth.

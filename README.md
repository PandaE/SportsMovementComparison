# Sports Movement Comparator

A desktop application for comparing user sports movements with standard reference videos.  
Currently supports badminton (clear shot) movement analysis.

## Features

- Import and preview user movement videos
- Select and preview standard movement videos
- Playback at normal and slow speeds
- Validate video duration and movement completeness
- Compare user and standard movements side by side
- Display overall score and key movement comparisons with suggestions

## Getting Started

### Prerequisites

- Python 3.7+
- Windows OS (recommended)

### Installation

1. Clone this repository:

   ```
   git clone https://github.com/yourusername/sports_movement_comparator.git
   cd sports_movement_comparator
   ```

2. Install dependencies:
   ```
   pip install -r requirements.txt
   ```

### Running the App

```
python main.py
```

## Project Structure

- `main.py` — Application entry point
- `ui/` — User interface modules
- `core/` — Core logic (video import, comparison, movement detection)
- `data/` — Data models and standard videos
- `assets/` — Icons and images
- `tests/` — Unit tests

## Future Work

- Implement pose detection and advanced comparison algorithms
- Add support for more sports and actions
- Enhance video playback and UI features

## New Evaluation Pipeline (Refactor)

This branch introduces a modular Metrics + Evaluation pipeline replacing the earlier frame-by-frame comparison focus.

Flow:

1. Pose Extraction (MediaPipe or mock fallback)
2. Metrics Engine (`MetricsEngine`) computes configured measurements per stage (angles, distances, heights, directional distances)
3. Evaluation Layer (`core/evaluation`) turns raw measurements into multi-stage scored feedback with localization (zh_CN / en_US) and optional incremental updates

Key Modules:

- `core/metrics_engine.py` – pluggable measurement handlers
- `core/evaluation/` – scoring strategies, feedback generation, incremental evaluation
- `core/pipeline/evaluation_pipeline.py` – high-level helpers (`run_action_evaluation`, `run_action_evaluation_incremental`)

Incremental Updates:

Use `evaluate_action_incremental` (wrapped by `run_action_evaluation_incremental`) to recompute only the stages whose frames changed instead of full reevaluation.

Experimental Engine Integration:

`ExperimentalComparisonEngine` now adds a `new_evaluation` section in its result dictionary containing unified evaluation output alongside legacy comparison results.

Migration Notes:

- Legacy `FrameComparator` remains for side-by-side differential analysis but is no longer required for producing scores.
- New evaluation config is auto-built from existing `sport_configs` tolerance ranges (converted to target ± tolerance and min/max bounds).
- To add a new measurement type: register a handler in `MetricsEngine` and reference it in sport configs.

Planned Enhancements:

- Confidence-weighted scoring
- Richer suggestion synthesis & trend tracking
- External LLM refinement plug-in (current stub only)

## License

MIT License

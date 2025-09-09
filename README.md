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

## License

MIT License

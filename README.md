# wr_tracker

## Getting started

From the root directory of the project: 

1. Install uv: `brew install uv`

2. Create a virtual environment: `uv sync`

3. Activate the virtual environment: `source .venv/bin/activate`

4. Run the main script: `cd src && python main_ui.py`

## Building the macOS app

From the root directory of the project: `nicegui-pack --name "WR Tracker" --windowed --onedir --icon assets/app.icns --osx-bundle-identifier com.wrtracker.app app.py`
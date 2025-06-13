# Fortnite Map Navigator

A terminal-based utility for exploring and searching Fortnite map version archives.

## Overview

The Fortnite Map Navigator provides an interactive TUI (Text User Interface) to browse, view, and search through Fortnite map version archives organized by chapter, season, and update version. It allows you to:

- Navigate through chapters, seasons, and update directories
- View JSON files with map location data
- Search for specific locations across all map versions
- See which chapters, seasons, and updates contain specific locations

```
┌─ Directory: /path/to/fortnite-archives ───────────────────────────────────┐
│ chapter_1/                                                                │
│ chapter_2/                                                                │
│                                                                           │
│                                                                           │
└─ Press q to quit, Enter to open, Backspace to up, f to search ────────────┘
```

## Installation

1. Make sure you have Python 3.6+ installed
2. Install the required dependencies:

```bash
pip install blessed
```

## Usage

Run the navigator from the project root:

```bash
python navigator/main.py
```

### Controls

- **Arrow keys**: Navigate through directories/files or search results
- **Enter**: Open selected directory or file
- **Backspace**: Go up a directory or return from file view
- **f**: Search for locations
- **q**: Quit the application
- **Page Up/Down**: Scroll through file content faster

## Project Structure

```
navigator/
├── core/           # Backend functionality
│   └── navigator.py  # File system and data operations
├── tui/            # Terminal User Interface
│   └── navigator.py  # User interaction and display logic
├── tests/          # Unit tests
├── main.py         # Entry point script
└── run_tests.py    # Test runner
```

## Expected Data Structure

The navigator expects your Fortnite archive data to be organized in the following structure:

```
fortnite-archives/
├── chapter_1/
│   ├── season_1/
│   │   ├── 1.6.0/
│   │   │   ├── 1.6.0.json  # JSON file with locations data
│   │   │   └── 1.6.0.jpg   # Optional map image
│   │   ├── 1.8.0/
│   │   │   ├── 1.8.0.json
│   │   │   └── 1.8.0.jpg
│   ├── season_2/
│   │   ├── 2.1.0/
...
```

### JSON File Format

The JSON files should contain at minimum a "locations" array with the named points of interest for that map version:

```json
{
  "locations": [
    "Tilted Towers",
    "Pleasant Park",
    "Retail Row",
    "Dusty Depot"
  ]
}
```

## Features

### Directory Navigation

Browse through the hierarchical structure of Fortnite map versions:
- Chapter directories
- Season directories within each chapter
- Update directories within each season
- JSON files containing location data

### File Viewing

View the contents of JSON files containing location data for each map version with a simple terminal-based viewer.

### Location Search

Search for specific locations across all map versions:
- Enter a search term with the 'f' key
- Results show which chapters/seasons contain matching locations
- Each result includes the specific update versions where matches were found
- Select a result to navigate directly to that chapter/season

## Development

### Running Tests

```bash
python navigator/run_tests.py
```

### Architecture

The navigator uses a clean separation between backend logic and UI:

- **Core Module**: Provides file system operations, directory navigation, and search functionality independent of the UI
- **TUI Module**: Handles user input, screen rendering, and state management for the terminal interface

This separation allows for potential future extensions like a GUI or web interface without changing the core functionality.

## License

This project is open source and available under the MIT License.

## Contributing

Pull requests are welcome! If you're adding new features or fixing bugs:

1. Make sure your code follows the existing style
2. Run the test suite with `python navigator/run_tests.py`
3. Update the README if you're adding new functionality
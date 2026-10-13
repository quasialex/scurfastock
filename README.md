# Scurfa Stock Watcher

A simple Python script that monitors the availability of the **Scurfa Diver One D1-500 ND Titanium Black (2025)** and sounds an alarm when a potential restock is detected.

Built to help catch limited stock releases without constantly refreshing the product page.

## Features

- Monitors the specific Scurfa product page and SKU.
- Checks availability every 120 seconds by default.
- Sounds a continuous alarm when a possible restock is detected.
- Supports Windows, Linux, and macOS.
- Configurable polling interval.
- No account or API key required.

## Installation

Requires Python 3 and two dependencies:

`pip install requests beautifulsoup4`

## Usage

Start monitoring:

`python3 scurfa_watch.py`

Use a custom polling interval (e.g., 5 minutes):

`python3 scurfa_watch.py --interval 300`

Test the alarm:

`python3 scurfa_watch.py --test-alarm`

Press **Ctrl+C** to stop monitoring or silence the alarm.

## Notes

- This is a best-effort stock watcher, not a guaranteed availability notification service.
- Changes to the website may cause false positives or break stock detection.
- Keep polling intervals reasonable to avoid unnecessary requests.
- On Linux, audio playback requires `paplay`, `aplay`, or `ffplay` (otherwise the script falls back to the terminal bell).

## Disclaimer

Unofficial community project. Not affiliated with or endorsed by Scurfa Watches.

Created for personal use and shared with fellow watch enthusiasts. Use responsibly.

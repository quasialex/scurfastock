#!/usr/bin/env python3
"""One-day stock watcher for Scurfa Diver One D1-500 ND Titanium Black.

Checks at a polite 120-second interval by default. Silent until a possible
restock is detected, then rings continuously until Ctrl+C.
"""

import argparse
import math
import os
import platform
import shutil
import struct
import subprocess
import sys
import tempfile
import time
import wave
from datetime import datetime

import requests
from bs4 import BeautifulSoup

URL = "https://www.scurfawatches.com/product/diver-one-d1-500-nd-titanium-black-2025/"
SKU = "D1-500-ND-TITANIUM-BLACK-25"


def check_stock(session):
    response = session.get(
        URL,
        timeout=18,
        headers={
            "User-Agent": "Mozilla/5.0 (compatible; personal-stock-watcher/1.0)",
            "Cache-Control": "no-cache",
            "Pragma": "no-cache",
        },
    )
    response.raise_for_status()
    soup = BeautifulSoup(response.text, "html.parser")
    page_text = soup.get_text(" ", strip=True)

    # Sanity-check the actual product, not a redirected error/catalog page.
    if SKU.lower() not in page_text.lower() or "Diver One D1-500 ND Titanium Black" not in page_text:
        return "ERROR", "Expected product or SKU missing; ignoring page."

    # Related products have their own 'Add to basket' buttons. Only the
    # WooCommerce SINGLE product's add-to-cart button is relevant.
    main_button = soup.select_one("button.single_add_to_cart_button, a.single_add_to_cart_button")
    button_enabled = bool(
        main_button
        and not main_button.has_attr("disabled")
        and "disabled" not in main_button.get("class", [])
        and main_button.get("aria-disabled", "false").lower() != "true"
    )

    summary = soup.select_one(".product .summary, .entry-summary")
    if summary:
        status_text = summary.get_text(" ", strip=True).lower()
    else:
        # The advertised stock status appears ahead of the product's SKU.
        status_text = page_text.lower().split(SKU.lower(), 1)[0][-1000:]

    if button_enabled and "awaiting stock" not in status_text:
        return "ALERT", "Product's own Add to Basket button is active."
    if "awaiting stock" in status_text:
        return "WAIT", "Awaiting Stock"
    if any(phrase in status_text for phrase in ("out of stock", "sold out", "unavailable")):
        return "WAIT", "Sold out / unavailable"
    if button_enabled or "in stock" in status_text:
        return "ALERT", "Product appears available."
    # On an otherwise valid product page, the disappearance of the exact
    # 'Awaiting Stock' message is worth waking the user immediately.
    return "ALERT", "Stock wording changed; inspect purchase button manually."


def write_bell_sound(filename):
    rate = 44100
    samples = []
    # Two short tones, then a brief pause; repeats until user stops script.
    for frequency, duration in ((1000, 0.22), (0, 0.11), (1250, 0.22), (0, 0.18)):
        for i in range(int(rate * duration)):
            if frequency:
                fade = min(1, i / 350, (int(rate * duration) - i) / 350)
                value = int(0.38 * 32767 * fade * math.sin(2 * math.pi * frequency * i / rate))
            else:
                value = 0
            samples.append(value)
    with wave.open(filename, "wb") as wav:
        wav.setnchannels(1)
        wav.setsampwidth(2)
        wav.setframerate(rate)
        wav.writeframes(struct.pack(f"<{len(samples)}h", *samples))


def alarm():
    with tempfile.TemporaryDirectory() as tmp:
        sound = os.path.join(tmp, "scurfa_alarm.wav")
        write_bell_sound(sound)
        system = platform.system()
        if system == "Windows":
            import winsound
            player = lambda: winsound.PlaySound(sound, winsound.SND_FILENAME)
        elif system == "Darwin" and shutil.which("afplay"):
            player = lambda: subprocess.run(["afplay", sound], check=False, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        else:
            programs = (
                ("paplay", ["paplay", sound]),
                ("aplay", ["aplay", "-q", sound]),
                ("ffplay", ["ffplay", "-nodisp", "-autoexit", "-loglevel", "quiet", sound]),
            )
            command = next((cmd for exe, cmd in programs if shutil.which(exe)), None)
            if command:
                def player():
                    completed = subprocess.run(command, check=False, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                    if completed.returncode != 0:
                        print("WARNING: Audio player failed. Falling back to terminal bell.", flush=True)
                        sys.stdout.write("\a")
                        sys.stdout.flush()
                        time.sleep(0.7)
            else:
                print("WARNING: No audio player found (paplay/aplay/ffplay). Terminal bell may be muted.", flush=True)
                player = lambda: (sys.stdout.write("\a"), sys.stdout.flush(), time.sleep(0.7))
        print("\n*** SCURFA STOCK ALERT — CHECK NOW! ***", flush=True)
        print(URL, flush=True)
        print("Ringing continuously. Press Ctrl+C to silence.\n", flush=True)
        while True:
            player()


def main():
    parser = argparse.ArgumentParser(description="Monitor only the Scurfa Titanium Black for availability.")
    parser.add_argument("--interval", type=int, default=120, help="Seconds between checks (default: 120)")
    parser.add_argument("--test-alarm", action="store_true", help="Test continuous sound without polling website")
    args = parser.parse_args()
    if args.interval < 60:
        parser.error("Please use an interval of at least 60 seconds.")

    try:
        if args.test_alarm:
            alarm()
            return
        print(f"Watching: {URL}")
        print(f"Checking every {args.interval} seconds. Silent until a stock change. Ctrl+C to stop.\n")
        with requests.Session() as session:
            while True:
                now = datetime.now().strftime("%H:%M:%S")
                try:
                    state, description = check_stock(session)
                except requests.RequestException as exc:
                    state, description = "ERROR", f"Request failed ({type(exc).__name__}); retrying."
                print(f"[{now}] {state}: {description}", flush=True)
                if state == "ALERT":
                    alarm()  # never returns until Ctrl+C
                time.sleep(args.interval)
    except KeyboardInterrupt:
        print("\nStopped.")


if __name__ == "__main__":
    main()

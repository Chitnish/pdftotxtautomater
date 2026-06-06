"""
watcher.py
----------
Watches a folder for new PDFs and auto-runs field extraction.

Usage:
    python watcher.py                        # watches ./inbox (default)
    python watcher.py /path/to/your/folder  # custom folder
"""

import sys
import time
import logging
from pathlib import Path
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from extract_fields import process_pdf

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
log = logging.getLogger(__name__)

WATCH_FOLDER = "./inbox"


class PDFHandler(FileSystemEventHandler):
    def __init__(self):
        self._seen = set()

    def on_created(self, event):
        self._handle(event.src_path)

    def on_moved(self, event):
        self._handle(event.dest_path)

    def _handle(self, path: str):
        p = Path(path)
        if p.suffix.lower() != ".pdf":
            return
        if path in self._seen:
            return
        self._seen.add(path)

        time.sleep(1.5)  # wait for file to finish writing
        log.info(f"New PDF detected: {p.name}")
        try:
            out = process_pdf(path)
            log.info(f"Done → {out}")
        except Exception as e:
            log.error(f"Failed to process {p.name}: {e}")


def main():
    folder = Path(sys.argv[1] if len(sys.argv) > 1 else WATCH_FOLDER)
    folder.mkdir(parents=True, exist_ok=True)

    log.info(f"Watching: {folder.resolve()}")
    log.info("Save a PDF into that folder and it will be processed automatically.")
    log.info("Press Ctrl+C to stop.\n")

    handler  = PDFHandler()
    observer = Observer()
    observer.schedule(handler, str(folder), recursive=False)
    observer.start()

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        log.info("Stopping...")
        observer.stop()
    observer.join()


if __name__ == "__main__":
    main()

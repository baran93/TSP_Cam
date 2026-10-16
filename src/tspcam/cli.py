"""TSP_Cam diagnostics CLI and Phase 0 supervisor."""
from __future__ import annotations

import argparse
import json
import logging
import signal
import threading

from .config import load_config
from .diagnostics import status
from .web import serve


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="tspcam", description="TSP_Cam Phase 0 diagnostics")
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("status", help="read-only JSON hardware and service status")
    agent = sub.add_parser("agent", help="periodic read-only system diagnostics")
    agent.add_argument("--interval", type=int, default=60)
    sub.add_parser("web", help="local-only read-only web diagnostics")
    args = parser.parse_args(argv)
    try:
        config = load_config()
    except (ValueError, OSError) as exc:
        parser.error(f"configuration: {exc}")
    if args.command == "status":
        print(json.dumps(status(config), indent=2, sort_keys=True))
        return 0
    if args.command == "web":
        serve(config)
        return 0
    if args.interval < 5 or args.interval > 3600:
        parser.error("--interval must be 5..3600 seconds")
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    stop = threading.Event()
    signal.signal(signal.SIGTERM, lambda _s, _f: stop.set())
    signal.signal(signal.SIGINT, lambda _s, _f: stop.set())
    while not stop.is_set():
        logging.info("%s", json.dumps(status(config), sort_keys=True))
        stop.wait(args.interval)
    return 0

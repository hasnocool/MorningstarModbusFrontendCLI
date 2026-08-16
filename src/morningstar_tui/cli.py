"""Command-line entry point for interactive and plain-text dashboard modes."""

from __future__ import annotations

import argparse
import asyncio
from collections.abc import Sequence
import json
from typing import Any

from morningstar_tui.config import AppConfig, apply_cli_overrides, load_config
from morningstar_tui.state import DashboardRuntime, SiteState
from morningstar_tui.util.formatting import first, fmt_number, metric, text


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="morningstar-tui",
        description="Terminal operations dashboard for MorningstarModbusAPI",
    )
    parser.add_argument("--config", help="TOML configuration file")
    parser.add_argument("--site", help="run only one configured site by name")
    parser.add_argument("--system", help="override system UID/name")
    parser.add_argument("--compact", action="store_true", help="prefer compact terminal presentation")
    parser.add_argument(
        "--low-bandwidth",
        action="store_true",
        help="increase REST refresh interval for constrained links",
    )
    parser.add_argument(
        "--alert-only",
        action="store_true",
        help="disable continuous SSE and poll the richer alert state only",
    )
    parser.add_argument(
        "--snapshot",
        action="store_true",
        help="print one ANSI-free console snapshot and exit",
    )
    parser.add_argument("--json", action="store_true", help="with --snapshot, emit JSON")
    parser.add_argument("--version", action="store_true", help="print version and exit")
    return parser


def _config(args: argparse.Namespace) -> AppConfig:
    config = load_config(args.config)
    return apply_cli_overrides(
        config,
        site=args.site,
        system=args.system,
        compact=True if args.compact else None,
        low_bandwidth=True if args.low_bandwidth else None,
        alert_only=True if args.alert_only else None,
    )


async def _snapshot(config: AppConfig, *, as_json: bool) -> int:
    runtime = DashboardRuntime(config)
    try:
        states = await runtime.snapshot_once()
    finally:
        await runtime.close()
    if as_json:
        print(json.dumps([_snapshot_payload(item) for item in states], indent=2, default=str))
    else:
        for state in states:
            print(_snapshot_text(state))
    return 0 if all(state.online for state in states) else 2


def _snapshot_payload(state: SiteState) -> dict[str, Any]:
    return {
        "site": state.name,
        "base_url": state.base_url,
        "system_uid": state.system_uid,
        "online": state.online,
        "stream_online": state.stream_online,
        "latency_ms": state.latency_ms,
        "health_score": first(state.health_score, "score", "health_score", "total"),
        "solar_input_power_w": metric(state.latest, "solar_input_power_w"),
        "battery_voltage_v": metric(state.latest, "battery_voltage_v"),
        "charge_state": metric(state.latest, "charge_state"),
        "active_incidents": len(state.incidents),
        "controllers": len(state.controllers),
        "error": state.last_error,
    }


def _snapshot_text(state: SiteState) -> str:
    payload = _snapshot_payload(state)
    lines = [
        f"Morningstar site: {payload['site']} ({payload['system_uid']})",
        f"API: {'ONLINE' if payload['online'] else 'OFFLINE'}  latency={fmt_number(payload['latency_ms'], 'ms', 0)}",
        f"Health: {fmt_number(payload['health_score'], '/100', 0)}",
        f"Solar: {fmt_number(payload['solar_input_power_w'], 'W', 0)}",
        f"Battery: {fmt_number(payload['battery_voltage_v'], 'V', 2)}",
        f"Charge stage: {text(payload['charge_state'])}",
        f"Controllers: {payload['controllers']}  active incidents: {payload['active_incidents']}",
    ]
    if payload["error"]:
        lines.append(f"Error: {payload['error']}")
    return "\n".join(lines) + "\n"


def main(argv: Sequence[str] | None = None) -> None:
    args = _parser().parse_args(argv)
    if args.version:
        from morningstar_tui import __version__

        print(__version__)
        raise SystemExit(0)
    try:
        config = _config(args)
    except (OSError, ValueError) as exc:
        raise SystemExit(f"configuration error: {exc}") from exc
    if args.snapshot:
        raise SystemExit(asyncio.run(_snapshot(config, as_json=args.json)))

    # Textual is imported only for interactive mode so plain snapshot mode stays useful
    # in minimal/headless environments.
    from morningstar_tui.app import MorningstarTUI

    MorningstarTUI(config).run()

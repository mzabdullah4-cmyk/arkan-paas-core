#!/usr/bin/env python3
"""Small local/VM status CLI for the Arkan repository and running app."""
import argparse
import json
import subprocess
import sys
import urllib.request
from pathlib import Path


def command(args):
    try:
        result = subprocess.run(args, text=True, capture_output=True, check=False)
        return result.returncode, result.stdout.strip() or result.stderr.strip()
    except FileNotFoundError:
        return 127, f"{args[0]} is not installed"


def url_status(url):
    try:
        with urllib.request.urlopen(url, timeout=5) as response:
            return response.status, response.read().decode("utf-8", errors="replace")
    except Exception as exc:
        return 0, str(exc)


def main():
    parser = argparse.ArgumentParser(description="Check Arkan repository and application status")
    parser.add_argument("--url", default="http://localhost:8080", help="Portal URL")
    parser.add_argument("--api-url", default="http://localhost:8000", help="Control-plane URL")
    parser.add_argument("--json", action="store_true", help="Emit machine-readable JSON")
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[1]
    git_code, git_output = command(["git", "-C", str(root), "status", "--short", "--branch"])
    compose_code, compose_output = command(["docker", "compose", "-f", str(root / "docker-compose.prod.yml"), "ps"])
    portal_code, portal_body = url_status(args.url)
    api_code, api_body = url_status(args.api_url + "/health")
    data = {"repository": {"ok": git_code == 0, "status": git_output}, "compose": {"ok": compose_code == 0, "status": compose_output}, "portal": {"ok": portal_code == 200, "status": portal_code or portal_body}, "api": {"ok": api_code == 200, "status": api_code or api_body}}
    if args.json:
        print(json.dumps(data, indent=2))
    else:
        for name, value in data.items(): print(f"{'OK' if value['ok'] else 'FAIL':4} {name}: {value['status']}")
    return 0 if all(value["ok"] for value in data.values()) else 1


if __name__ == "__main__":
    sys.exit(main())

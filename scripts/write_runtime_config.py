from __future__ import annotations

import argparse
import json
import os
from pathlib import Path


def main() -> None:
    parser = argparse.ArgumentParser(description="Write browser runtime config for the frontend.")
    parser.add_argument("--output", default="frontend/dist/config.js")
    args = parser.parse_args()

    config = {
        "apiBase": os.environ.get("VITE_API_BASE", "").strip().rstrip("/"),
        "frontendPublicUrl": os.environ.get("FRONTEND_PUBLIC_URL", "").strip().rstrip("/"),
    }

    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(
        "window.__APP_CONFIG__ = " + json.dumps(config, ensure_ascii=False) + ";\n",
        encoding="utf-8",
    )
    print(f"runtime config written: {output}")
    print(json.dumps(config, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()

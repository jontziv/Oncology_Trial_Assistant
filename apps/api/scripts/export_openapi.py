import json
from pathlib import Path

from copilot.main import app


def main() -> None:
    output = Path(__file__).parents[3] / "packages" / "api-client" / "openapi.json"
    output.write_text(json.dumps(app.openapi(), indent=2, sort_keys=True) + "\n")


if __name__ == "__main__":
    main()


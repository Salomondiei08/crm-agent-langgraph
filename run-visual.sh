#!/bin/sh
set -eu

PROJECT_DIR=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
cd "$PROJECT_DIR"
export LANGGRAPH_USE_OPENAI="${LANGGRAPH_USE_OPENAI:-true}"

if [ ! -x .venv/bin/python ]; then
  echo "Environment missing. Run: python3 -m venv .venv && .venv/bin/pip install -r requirements.txt" >&2
  exit 1
fi

exec .venv/bin/python -m lab.web "$@"

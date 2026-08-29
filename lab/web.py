"""Small standard-library web server for the visual LangGraph lesson."""
import json
import argparse
import webbrowser
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse

from langgraph.types import Command

from .graph import build_graph

WEB_ROOT = Path(__file__).parent.parent / "web"
GRAPH = build_graph()


def _state_payload(result: dict) -> dict:
    """Convert a LangGraph result into a browser-friendly teaching payload."""
    interrupt = result.get("__interrupt__")
    if interrupt:
        request = interrupt[0].value
        return {
            "status": "paused",
            "draft": request["draft"],
            "events": result.get("events", []),
            "category": result.get("category"),
            "state": result,
        }
    return {
        "status": "completed",
        "draft": result.get("final_reply", ""),
        "events": result.get("events", []),
        "category": result.get("category"),
        "state": result,
    }


class LessonHandler(BaseHTTPRequestHandler):
    """Serve the lesson UI and two JSON endpoints."""

    def _send_json(self, payload: dict, status: int = 200) -> None:
        body = json.dumps(payload, ensure_ascii=False, default=str).encode()
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self) -> None:  # noqa: N802 - required by BaseHTTPRequestHandler
        requested_path = urlparse(self.path).path
        file_name = "index.html" if requested_path == "/" else requested_path.lstrip("/")
        if file_name not in {"index.html", "style.css", "app.js"}:
            self.send_error(404)
            return
        body = (WEB_ROOT / file_name).read_bytes()
        self.send_response(200)
        content_types = {"index.html": "text/html; charset=utf-8", "style.css": "text/css", "app.js": "text/javascript"}
        self.send_header("Content-Type", content_types[file_name])
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_POST(self) -> None:  # noqa: N802 - required by BaseHTTPRequestHandler
        length = int(self.headers.get("Content-Length", 0))
        payload = json.loads(self.rfile.read(length) or b"{}")
        path = urlparse(self.path).path
        try:
            if path == "/api/run":
                thread_id = payload.get("thread_id", "browser-demo")
                result = GRAPH.invoke(
                    {"ticket": payload["ticket"], "events": []},
                    {"configurable": {"thread_id": thread_id}},
                )
            elif path == "/api/resume":
                config = {"configurable": {"thread_id": payload["thread_id"]}}
                result = GRAPH.invoke(Command(resume=payload["decision"]), config)
            else:
                self._send_json({"error": "Unknown endpoint"}, 404)
                return
            self._send_json(_state_payload(result))
        except (KeyError, json.JSONDecodeError, ValueError) as error:
            self._send_json({"error": str(error)}, 400)


def serve(port: int = 8765, open_browser: bool = True) -> None:
    """Start the visual lesson server."""
    try:
        server = ThreadingHTTPServer(("127.0.0.1", port), LessonHandler)
    except OSError as error:
        raise SystemExit(
            f"Cannot start on port {port}. Close the existing lesson server or use --port 8766. ({error})"
        ) from error
    url = f"http://127.0.0.1:{port}"
    print(f"LangGraph Teaching Lab is ready: {url}", flush=True)
    print("Keep this terminal open. Press Ctrl+C to stop.", flush=True)
    if open_browser:
        webbrowser.open(url)
    server.serve_forever()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run the visual LangGraph lesson")
    parser.add_argument("--port", type=int, default=8765)
    parser.add_argument("--no-open", action="store_true", help="Do not open a browser automatically")
    arguments = parser.parse_args()
    serve(arguments.port, not arguments.no_open)

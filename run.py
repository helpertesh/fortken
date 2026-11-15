"""Start the website with Waitress (works on Windows and Linux).

    python run.py

For development with auto-reload use:  flask --app app run --debug
"""
import os

from waitress import serve

from app import create_app

app = create_app()

if __name__ == "__main__":
    host = os.environ.get("HOST", "127.0.0.1")
    port = int(os.environ.get("PORT", "8000"))
    print(f"KF 4Fortken website running on http://{host}:{port}  (admin: http://{host}:{port}/admin)")
    serve(app, host=host, port=port)

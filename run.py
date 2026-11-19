
"""
Start the KF 4Fortken Flask website.

For local development:
    python run.py

For development with auto-reload:
    flask --app run run --debug
"""

import os

from app import create_app

app = create_app()

if __name__ == "__main__":
    host = os.environ.get("HOST", "127.0.0.1")
    port = int(os.environ.get("PORT", "8000"))

    print(
        f"KF 4Fortken website running on http://{host}:{port} "
        f"(admin: http://{host}:{port}/admin)"
    )

    app.run(host=host, port=port, debug=False)
"""Script to capture desktop (1440x900) and mobile (390x844) screenshots using headless Chrome (Task 5 / Phase 5 Gate)."""
import os
from pathlib import Path
import subprocess
import time
import urllib.request

ROOT = Path(__file__).resolve().parent.parent
SCREENSHOT_DIR = ROOT / "evidence" / "screenshots"
SCREENSHOT_DIR.mkdir(parents=True, exist_ok=True)

CHROME_PATH = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
if not os.path.exists(CHROME_PATH):
    CHROME_PATH = r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"


def wait_for_server(url: str, timeout: int = 15) -> bool:
    start = time.time()
    while time.time() - start < timeout:
        try:
            with urllib.request.urlopen(url, timeout=2) as response:
                if response.status == 200:
                    return True
        except Exception:
            time.sleep(0.5)
    return False


def main():
    print(f"Using browser at: {CHROME_PATH}")
    port = 8000
    server_url = f"http://localhost:{port}"

    # Launch uvicorn server
    env = os.environ.copy()
    env["PYTHONUNBUFFERED"] = "1"
    server_proc = subprocess.Popen(
        [
            str(ROOT / ".venv" / "Scripts" / "python.exe"),
            "-m",
            "uvicorn",
            "api.app:app",
            "--host",
            "127.0.0.1",
            "--port",
            str(port),
        ],
        cwd=str(ROOT),
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )

    try:
        print("Waiting for Medantrik Assist server to start...")
        if not wait_for_server(f"{server_url}/health"):
            print("Server failed to respond to /health in time.")
            return

        print("Server is ready. Capturing screenshots...")
        # 1. Desktop 1440x900
        desktop_img = SCREENSHOT_DIR / "desktop_1440x900.png"
        subprocess.run(
            [
                CHROME_PATH,
                "--headless=new",
                "--disable-gpu",
                "--hide-scrollbars",
                f"--window-size=1440,900",
                f"--screenshot={str(desktop_img)}",
                server_url,
            ],
            check=True,
            timeout=30,
        )
        print(f"Captured: {desktop_img} ({desktop_img.stat().st_size} bytes)")

        # 2. Mobile 390x844
        mobile_img = SCREENSHOT_DIR / "mobile_390x844.png"
        subprocess.run(
            [
                CHROME_PATH,
                "--headless=new",
                "--disable-gpu",
                "--hide-scrollbars",
                f"--window-size=390,844",
                f"--screenshot={str(mobile_img)}",
                server_url,
            ],
            check=True,
            timeout=30,
        )
        print(f"Captured: {mobile_img} ({mobile_img.stat().st_size} bytes)")

    finally:
        server_proc.terminate()
        try:
            server_proc.wait(timeout=5)
        except subprocess.TimeoutExpired:
            server_proc.kill()
        print("Server stopped cleanly.")


if __name__ == "__main__":
    main()

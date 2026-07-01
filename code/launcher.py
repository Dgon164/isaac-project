"""
Isaac — Launcher
Opens the GUI in a native window (pywebview) or your default browser.

Usage:
    python launcher.py              # native window or browser
    python launcher.py --browser    # force browser mode
"""

import sys
import threading
import time


def main():
    browser_mode = "--browser" in sys.argv

    # Start Flask in a background thread
    from app import app

    def run_flask():
        app.run(host="127.0.0.1", port=5050, debug=False, use_reloader=False)

    server = threading.Thread(target=run_flask, daemon=True)
    server.start()

    url = "http://127.0.0.1:5050"
    time.sleep(0.5)  # let Flask start

    if not browser_mode:
        try:
            import webview
            window = webview.create_window(
                "Isaac", url,
                width=1200, height=800,
                min_size=(800, 500),
                text_select=True,
            )
            webview.start()
            return
        except ImportError:
            pass

    # Fallback: open in browser
    import webbrowser
    webbrowser.open(url)
    print(f"Isaac running at {url}")
    print("Press Ctrl+C to stop.")
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\nGoodbye.")


if __name__ == "__main__":
    main()

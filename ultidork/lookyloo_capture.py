# ultidork/lookyloo_capture.py

from ultidork.lookyloo.lookyloo import Lookyloo
import time

def capture_url(url):
    l = Lookyloo()
    capture_uuid = l.enqueue_capture({"url": url}, source="ultidork", user="ultidork", authenticated=True)
    print(f"[lookyloo] Capture UUID: {capture_uuid}")

    # Wait for the capture to complete
    while True:
        status = l.get_capture_status(capture_uuid)
        print(f"[lookyloo] Status: {status}")
        if status.name == "DONE":
            break
        elif status.name == "UNKNOWN":
            raise RuntimeError("Capture failed or never queued.")
        time.sleep(3)

    # Fetch result data (HTML, screenshot, stats)
    html = l.get_html(capture_uuid).read()
    screenshot = l.get_screenshot(capture_uuid).read()
    stats = l.get_statistics(capture_uuid)
    return {
        "uuid": capture_uuid,
        "html": html,
        "screenshot": screenshot,
        "stats": stats,
    }

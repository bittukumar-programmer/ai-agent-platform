from playwright.sync_api import sync_playwright
from concurrent.futures import ThreadPoolExecutor

# A single dedicated thread that owns the browser forever — Playwright's sync API
# requires every call to happen on the exact same thread it was started on.
_executor = ThreadPoolExecutor(max_workers=1)

_playwright = None
_browser = None
_page = None


def _get_page():
    global _playwright, _browser, _page
    if _page is None:
        _playwright = sync_playwright().start()
        _browser = _playwright.chromium.launch(
            headless=False,
            args=["--disable-blink-features=AutomationControlled"],  # hide the "automated browser" signal
        )
        context = _browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
            viewport={"width": 1280, "height": 800},
        )
        _page = context.new_page()
    return _page


def _run_on_browser_thread(func):
    """Submits a function to the dedicated browser thread and waits for the result."""
    future = _executor.submit(func)
    return future.result()


def open_url(url: str) -> str:
    def _task():
        try:
            target = url if url.startswith("http") else "https://" + url
            page = _get_page()
            page.goto(target, timeout=15000)
            return f"Opened {target}"
        except Exception as e:
            return f"Error opening URL: {e}"
    return _run_on_browser_thread(_task)


def search_google(query: str) -> str:
    def _task():
        try:
            page = _get_page()
            page.goto(f"https://www.google.com/search?q={query.replace(' ', '+')}", timeout=15000)
            return f"Searched Google for '{query}'"
        except Exception as e:
            return f"Error searching: {e}"
    return _run_on_browser_thread(_task)


def search_youtube(query: str) -> str:
    def _task():
        try:
            page = _get_page()
            if "youtube.com" not in page.url:
                page.goto("https://www.youtube.com", timeout=15000)
            search_box = page.locator('input[name="search_query"]')
            search_box.fill(query, timeout=8000)
            search_box.press("Enter")
            return f"Searched YouTube for '{query}'"
        except Exception as e:
            return f"Error searching YouTube: {e}"
    return _run_on_browser_thread(_task)

def click_first_youtube_result() -> str:
    """Clicks the first actual video result on a YouTube search results page."""
    def _task():
        try:
            page = _get_page()
            # YouTube video links use this specific structure, far more reliable than text matching
            first_video = page.locator("ytd-video-renderer a#video-title, ytd-video-renderer a#thumbnail").first
            first_video.scroll_into_view_if_needed(timeout=5000)
            first_video.click(timeout=8000)
            return "Playing the first video from the search results"
        except Exception as e:
            return f"Error opening first video: {e}"
    return _run_on_browser_thread(_task)


def click_text(text: str) -> str:
    def _task():
        try:
            page = _get_page()
            page.get_by_text(text, exact=False).first.click(timeout=8000)
            return f"Clicked on '{text}'"
        except Exception as e:
            return f"Error clicking '{text}': {e}"
    return _run_on_browser_thread(_task)


def type_text(placeholder_or_label: str, value: str) -> str:
    def _task():
        try:
            page = _get_page()
            field = page.get_by_placeholder(placeholder_or_label, exact=False).first
            field.fill(value, timeout=8000)
            return f"Typed '{value}' into field matching '{placeholder_or_label}'"
        except Exception as e:
            return f"Error typing into field: {e}"
    return _run_on_browser_thread(_task)


def read_page_text() -> str:
    def _task():
        try:
            page = _get_page()
            return page.inner_text("body")[:1500]
        except Exception as e:
            return f"Error reading page: {e}"
    return _run_on_browser_thread(_task)
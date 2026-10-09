from playwright.sync_api import sync_playwright

_playwright = None
_browser = None
_page = None


def _ensure_browser():
    """Starts the browser once, and reuses the same window across calls."""
    global _playwright, _browser, _page
    if _page is None:
        _playwright = sync_playwright().start()
        _browser = _playwright.chromium.launch(headless=False)  # headless=False so you can SEE it working
        _page = _browser.new_page()
    return _page


def open_url(url: str) -> str:
    """Opens a website in the browser."""
    try:
        if not url.startswith("http"):
            url = "https://" + url
        page = _ensure_browser()
        page.goto(url, timeout=15000)
        return f"Opened {url}"
    except Exception as e:
        return f"Error opening URL: {e}"


def search_google(query: str) -> str:
    """Searches Google for the given query."""
    try:
        page = _ensure_browser()
        page.goto(f"https://www.google.com/search?q={query.replace(' ', '+')}", timeout=15000)
        return f"Searched Google for '{query}'"
    except Exception as e:
        return f"Error searching: {e}"


def search_youtube(query: str) -> str:
    """Searches within YouTube's own search box (use when already on or going to YouTube)."""
    try:
        page = _ensure_browser()
        if "youtube.com" not in page.url:
            page.goto("https://www.youtube.com", timeout=15000)
        search_box = page.locator('input[name="search_query"]')
        search_box.fill(query, timeout=8000)
        search_box.press("Enter")
        return f"Searched YouTube for '{query}'"
    except Exception as e:
        return f"Error searching YouTube: {e}"


def click_text(text: str) -> str:
    """Clicks on an element containing the given visible text."""
    try:
        page = _ensure_browser()
        page.get_by_text(text, exact=False).first.click(timeout=8000)
        return f"Clicked on '{text}'"
    except Exception as e:
        return f"Error clicking '{text}': {e}"


def type_text(placeholder_or_label: str, value: str) -> str:
    """Types text into an input field identified by its placeholder or nearby label."""
    try:
        page = _ensure_browser()
        field = page.get_by_placeholder(placeholder_or_label, exact=False).first
        field.fill(value, timeout=8000)
        return f"Typed '{value}' into field matching '{placeholder_or_label}'"
    except Exception as e:
        return f"Error typing into field: {e}"


def read_page_text() -> str:
    """Reads the visible text of the current page (trimmed)."""
    try:
        page = _ensure_browser()
        text = page.inner_text("body")
        return text[:1500]  # keep it short enough for the LLM to read
    except Exception as e:
        return f"Error reading page: {e}"
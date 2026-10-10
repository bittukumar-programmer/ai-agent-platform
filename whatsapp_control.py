from playwright.sync_api import sync_playwright
from concurrent.futures import ThreadPoolExecutor
import os

_executor = ThreadPoolExecutor(max_workers=1)
_playwright = None
_browser_context = None
_page = None

USER_DATA_DIR = os.path.join(os.path.expanduser("~"), "aura_whatsapp_session")


def _get_page():
    global _playwright, _browser_context, _page
    if _page is None:
        _playwright = sync_playwright().start()
        _browser_context = _playwright.chromium.launch_persistent_context(
            USER_DATA_DIR, headless=False
        )
        _page = _browser_context.pages[0] if _browser_context.pages else _browser_context.new_page()
        _page.goto("https://web.whatsapp.com", timeout=60000)
    return _page


def _run(func):
    return _executor.submit(func).result()


def get_unread_chats() -> str:
    """Returns a summary of chats with unread messages."""
    def _task():
        try:
            page = _get_page()
            page.wait_for_selector('[data-testid="cell-frame-container"]', timeout=30000)
            all_chats = page.locator('[data-testid="cell-frame-container"]')
            count = all_chats.count()
            unread_names = []
            for i in range(count):
                chat = all_chats.nth(i)
                unread_badge = chat.locator('[aria-label*="unread message"]')
                if unread_badge.count() > 0:
                    name = chat.locator('[dir="auto"]').first.inner_text(timeout=2000)
                    unread_names.append(name)

            if not unread_names:
                return "No unread messages."
            return "Unread messages from: " + ", ".join(unread_names)
        except Exception as e:
            return f"Error checking WhatsApp: {e}"
    return _run(_task)


def read_chat(contact_name: str) -> str:
    """Opens a chat and reads the last few messages."""
    def _task():
        try:
            page = _get_page()
            page.get_by_text(contact_name, exact=False).first.click(timeout=8000)
            page.wait_for_timeout(1000)
            messages = page.locator('.message-in, .message-out').all_inner_texts()
            last_messages = messages[-5:] if messages else []
            return f"Last messages with {contact_name}:\n" + "\n".join(last_messages)
        except Exception as e:
            return f"Error reading chat: {e}"
    return _run(_task)


def send_whatsapp_message(contact_name: str, message: str) -> str:
    """Sends a message in an already-open chat with the given contact."""
    def _task():
        try:
            page = _get_page()
            page.get_by_text(contact_name, exact=False).first.click(timeout=8000)
            page.wait_for_timeout(500)
            box = page.locator('[aria-label="Type a message"]')
            box.click()
            box.fill(message)
            box.press("Enter")
            return f"Sent to {contact_name}: '{message}'"
        except Exception as e:
            return f"Error sending message: {e}"
    return _run(_task)


def debug_dump_chat_list() -> str:
    """Diagnostic: dumps the aria-labels of the first few chat list items, to help fix selectors."""
    def _task():
        try:
            page = _get_page()
            page.wait_for_timeout(2000)
            items = page.locator('[data-testid="cell-frame-container"]')
            count = items.count()
            output = [f"Found {count} list items.\n"]
            for i in range(min(count, 5)):
                html = items.nth(i).inner_html(timeout=3000)
                output.append(f"--- Item {i} ---\n{html[:500]}\n")
            return "\n".join(output)
        except Exception as e:
            return f"Error dumping chat list: {e}"
    return _run(_task)
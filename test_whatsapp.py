from whatsapp_control import _get_page

page = _get_page()
print("WhatsApp Web load ho raha hai, 15 second wait kar rahe hain...")
page.wait_for_timeout(15000)

page.screenshot(path="whatsapp_debug.png")
print("Screenshot saved as whatsapp_debug.png")

items = page.locator('div[role="listitem"]')
count = items.count()
print(f"Found {count} list items.")

page.context.close()
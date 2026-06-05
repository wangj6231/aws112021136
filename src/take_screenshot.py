from playwright.sync_api import sync_playwright

def run():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        # Navigate to the Vercel app
        print("Navigating to https://aws112021136.vercel.app/...")
        try:
            page.goto("https://aws112021136.vercel.app/", timeout=30000)
            # Wait for the main chart or content to load
            page.wait_for_timeout(5000) # wait 5 seconds for React/Charts to render
            
            # Take a full page screenshot
            print("Taking screenshot...")
            screenshot_path = r"C:\Users\milo9\Desktop\aws112021136\src\vercel_screenshot.png"
            page.screenshot(path=screenshot_path, full_page=True)
            print(f"Screenshot saved to {screenshot_path}")
        except Exception as e:
            print(f"Error taking screenshot: {e}")
        finally:
            browser.close()

if __name__ == "__main__":
    run()

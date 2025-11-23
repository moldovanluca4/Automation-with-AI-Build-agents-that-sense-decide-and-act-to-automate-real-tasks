from playwright.sync_api import sync_playwright
import time

def scrape_duckduckgo():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        page = browser.new_page()

        try:
            
            print("Choosing duckduckgo")
            page.goto("https://duckduckgo.com")

            
            page.locator('input[name="q"]').fill("top LMS EdTech competitors list")
            page.keyboard.press("Enter")

            
            page.wait_for_selector("li[data-layout='organic']", timeout=5000)

            results = []
            search_results = page.locator("li[data-layout='organic']").all()

            for result in search_results:
                title_loc = result.locator("h2 a").first
                link_loc = result.locator("h2 a").first 

                if title_loc.count() > 0:
                    name = title_loc.inner_text()
                    url = link_loc.get_attribute("href")
                    results.append({"name": name, "url": url})

            print("\n Printing some websites we got")
            for item in results:
                print(f"{item['name']} : {item['url']}")

        except Exception as e:
            print(f"Error: {e}")
        finally:
            browser.close()

if __name__ == "__main__":
    scrape_duckduckgo()
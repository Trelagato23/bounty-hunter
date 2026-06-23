import asyncio
from playwright.async_api import async_playwright
import json

async def scrape_hackerone():
    async with async_playwright() as p:
        # Launch browser (headless for homelab efficiency)
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        )
        page = await context.new_page()
        
        print("Scraping HackerOne with Playwright...")
        
        # Go to the directory page
        await page.goto("https://hackerone.com/directory/programs", wait_until="networkidle")
        
        # Wait for the program list to load
        await page.wait_for_selector(".daisy-table")
        
        # Extract program names and bounty status
        programs = await page.evaluate("""() => {
            const rows = Array.from(document.querySelectorAll('tr'));
            return rows.map(row => {
                const name = row.querySelector('strong')?.innerText;
                const bounty = row.innerText.includes('Bounties');
                return { name, bounty, platform: 'hackerone' };
            }).filter(p => p.name);
        }""")
        
        await browser.close()
        return programs

if __name__ == "__main__":
    results = asyncio.run(scrape_hackerone())
    print(json.dumps(results, indent=2))

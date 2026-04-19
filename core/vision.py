import asyncio
from playwright.async_api import async_playwright
from pathlib import Path

async def capture_screenshot(url: str, output_path: Path):
    """
    Captures a high-resolution screenshot of the given URL.
    """
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        # Use a premium device descriptor (large desktop)
        context = await browser.new_context(
            viewport={'width': 1440, 'height': 900},
            device_scale_factor=1 # Standard resolution for stability
        )
        page = await context.new_page()
        
        print(f"👁️  Specter navigating to {url}...")
        await page.goto(url, wait_until="networkidle")
        
        # Wait a bit for any animations to finish
        await asyncio.sleep(2)
        
        output_path.parent.mkdir(parents=True, exist_ok=True)
        await page.screenshot(path=str(output_path), full_page=False)
        print(f"📸 Snapshot captured: {output_path}")
        
        await browser.close()
        return output_path

def sync_capture_screenshot(url: str, output_path: Path):
    """Synchronous wrapper for capture_screenshot."""
    return asyncio.run(capture_screenshot(url, output_path))

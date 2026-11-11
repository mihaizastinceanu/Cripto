"""Reproduce the attack steps in the Crypto Corner frequency-analysis tool
(https://crypto.interactive-maths.com/frequency-analysis-breaking-the-code.html)
and save a screenshot of the tool after each step (img/site_*.png)."""
from pathlib import Path

from playwright.sync_api import sync_playwright

from frequency_attack import CIPHER, STEPS

URL = "https://crypto.interactive-maths.com/frequency-analysis-breaking-the-code.html"
HERE = Path(__file__).parent


def main():
    with sync_playwright() as p:
        browser = p.chromium.launch(channel="chrome")
        page = browser.new_page(viewport={"width": 1300, "height": 1000})
        # keep only the site itself: ads/overlays would cover the tool in the screenshots
        page.route("**/*", lambda r: r.continue_() if "interactive-maths.com" in r.request.url else r.abort())
        page.goto(URL, wait_until="load", timeout=90000)
        page.fill("#intercept", CIPHER)
        page.evaluate("""() => {
            document.querySelectorAll('ins, iframe, [id*=google], [class*=adsbygoogle]').forEach(e => e.remove());
            document.getElementById('intercept').rows = 8;
            document.getElementById('decryptedTxt').rows = 22;
        }""")
        page.click("#frequencyBtn")
        page.wait_for_timeout(800)
        tool = page.locator("div.wcustomhtml", has=page.locator("#intercept"))
        tool.screenshot(path=str(HERE / "img" / "site_0_frecvente.png"))
        order = [page.input_value(f"#origLetter_{i}") for i in range(26)]
        slot = {letter: i for i, letter in enumerate(order)}
        key = {}
        for n, (subs, _) in enumerate(STEPS, 1):
            key.update(subs)
            for c, plain in subs.items():
                page.fill(f"#subsLetter_{slot[c]}", plain)
            page.click("#substitutionsBtn")
            page.wait_for_timeout(500)
            tool.screenshot(path=str(HERE / "img" / f"site_{n}.png"))
        browser.close()


if __name__ == "__main__":
    main()

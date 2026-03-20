"""
Blog style analyzer.
Crawls recent posts, extracts formatting patterns, saves style_profile.json.
"""
import os, time, json, re
from datetime import datetime
from bs4 import BeautifulSoup
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
STYLE_PROFILE_PATH = os.path.join(ROOT, "style_profile.json")


def analyze_blog_style(driver, blog_id: str, post_count: int = 10) -> dict:
    """
    Crawl blog_id's recent posts and extract formatting style.
    Returns style_profile dict and saves it to style_profile.json.
    """
    # ── 1. Collect post URLs from blog main page ──────────────────────────────
    driver.get(f"https://blog.naver.com/{blog_id}")
    WebDriverWait(driver, 10).until(
        lambda d: d.execute_script("return document.readyState") == "complete"
    )
    time.sleep(1)

    post_urls = []
    try:
        iframe = driver.find_element(By.ID, "mainFrame")
        driver.switch_to.frame(iframe)
        time.sleep(1)
        links = driver.find_elements(
            By.CSS_SELECTOR, "a[href*='PostView.naver'][href*='logNo=']"
        )
        seen = set()
        for l in links:
            href = l.get_attribute("href") or ""
            if href and href not in seen:
                seen.add(href)
                if href.startswith("/"):
                    href = "https://blog.naver.com" + href
                post_urls.append(href)
            if len(post_urls) >= post_count:
                break
        driver.switch_to.default_content()
    except Exception:
        driver.switch_to.default_content()

    if not post_urls:
        return {"error": "no post URLs found"}

    # ── 2. Parse each post ────────────────────────────────────────────────────
    all_paragraphs = []        # sentence counts per post
    bold_examples = []         # text inside .se-bold spans
    highlight_examples = []    # text inside background-color spans
    text_color_examples = []   # text inside color spans (non-black)
    highlight_colors = set()
    text_colors = set()
    paragraph_counts = []

    for url in post_urls:
        try:
            driver.get(url)
            WebDriverWait(driver, 10).until(
                lambda d: d.execute_script("return document.readyState") == "complete"
            )
            time.sleep(0.8)

            soup = BeautifulSoup(driver.page_source, "lxml")

            # Paragraph structure
            paras = soup.select(".se-text-paragraph")
            paragraph_counts.append(len(paras))

            for para in paras:
                text = para.get_text(strip=True)
                if not text:
                    continue
                # rough sentence count by Korean/English period endings
                sentences = len(re.findall(r'[.。!?！？]+', text)) or 1
                all_paragraphs.append(sentences)

            # Bold examples
            for span in soup.select(".se-bold"):
                t = span.get_text(strip=True)
                if t and len(t) <= 50:
                    bold_examples.append(t)

            # Highlight (background-color) examples
            for span in soup.select("span[style]"):
                style = span.get("style", "")
                if "background-color" in style:
                    color_match = re.search(r'background-color\s*:\s*(#[0-9a-fA-F]{3,6}|rgb[^;)]+)', style)
                    if color_match:
                        highlight_colors.add(color_match.group(1).strip())
                    t = span.get_text(strip=True)
                    if t and len(t) <= 80:
                        highlight_examples.append(t)

            # Text color examples (non-black, non-default)
            for span in soup.select("span[style]"):
                style = span.get("style", "")
                if "color" in style and "background-color" not in style:
                    color_match = re.search(r'(?<!background-)color\s*:\s*(#[0-9a-fA-F]{3,6})', style)
                    if color_match:
                        c = color_match.group(1).lower()
                        if c not in ("#000000", "#000", "#333333", "#333"):
                            text_colors.add(c)
                            t = span.get_text(strip=True)
                            if t and len(t) <= 80:
                                text_color_examples.append(t)

        except Exception:
            continue

    # ── 3. Build profile ──────────────────────────────────────────────────────
    avg_sentences = round(sum(all_paragraphs) / len(all_paragraphs), 1) if all_paragraphs else 2.0
    avg_paragraphs = round(sum(paragraph_counts) / len(paragraph_counts), 1) if paragraph_counts else 8.0

    profile = {
        "analyzed_at": datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ"),
        "blog_id": blog_id,
        "post_count_analyzed": len(post_urls),
        "paragraph": {
            "avg_sentences": avg_sentences,
            "avg_per_post": avg_paragraphs,
        },
        "bold": {
            "count": len(bold_examples),
            "examples": bold_examples[:20],
        },
        "highlight": {
            "count": len(highlight_examples),
            "colors": sorted(highlight_colors),
            "examples": highlight_examples[:20],
        },
        "text_color": {
            "count": len(text_color_examples),
            "colors": sorted(text_colors),
            "examples": text_color_examples[:20],
        },
    }

    with open(STYLE_PROFILE_PATH, "w", encoding="utf-8") as f:
        json.dump(profile, f, ensure_ascii=False, indent=2)

    return profile

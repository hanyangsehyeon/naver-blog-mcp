"""
Blog analyzer.
Two-step flow:
  1. fetch_post_urls        — collect categories + URLs → url_index/{blog_id}.json
  2. create_examples_from_index — crawl selected categories → examples/{blog_id}/{category}/YYYYMMDD.json
"""
import os, time, json, re
from datetime import datetime, timezone
from bs4 import BeautifulSoup, NavigableString, Tag
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.common.exceptions import NoSuchElementException, TimeoutException

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
EXAMPLES_DIR = os.path.join(ROOT, "examples")
URL_INDEX_DIR = os.path.join(ROOT, "url_index")


# ── Paragraph → JSON converter ────────────────────────────────────────────────

def _para_to_json(para: Tag) -> dict | None:
    """
    Convert a .se-text-paragraph BeautifulSoup tag into paragraph JSON format:
    {"text": "...", "formatting": [{"type": ..., "start": ..., "end": ..., "color": ...}]}
    Returns None if paragraph is empty.
    """
    formatting = []
    full_text = []
    offset = 0

    def walk(node):
        nonlocal offset
        if isinstance(node, NavigableString):
            t = str(node)
            full_text.append(t)
            offset += len(t)
            return

        if not isinstance(node, Tag):
            return

        start = offset
        for child in node.children:
            walk(child)
        end = offset

        if start == end:
            return

        style = node.get("style", "")
        tag = node.name.lower() if node.name else ""

        is_bold = tag in ("strong", "b") or ("font-weight" in style and "bold" in style)
        bg_match = re.search(r'background-color\s*:\s*(#[0-9a-fA-F]{3,6})', style)
        fg_match = re.search(r'(?<!background-)color\s*:\s*(#[0-9a-fA-F]{3,6})', style)

        if bg_match:
            formatting.append({"type": "highlight", "start": start, "end": end, "color": bg_match.group(1)})
        if fg_match:
            c = fg_match.group(1).lower()
            if c not in ("#000000", "#000", "#333333", "#333", "#0a0a0a"):
                formatting.append({"type": "text_color", "start": start, "end": end, "color": c})
        if is_bold and not bg_match:
            formatting.append({"type": "bold", "start": start, "end": end})

    for child in para.children:
        walk(child)

    text = "".join(full_text).strip()
    if not text:
        return None

    stripped_start = len("".join(full_text)) - len("".join(full_text).lstrip())
    if stripped_start:
        formatting = [
            {**f, "start": f["start"] - stripped_start, "end": f["end"] - stripped_start}
            for f in formatting
            if f["end"] > stripped_start
        ]
        formatting = [{**f, "start": max(0, f["start"])} for f in formatting]

    return {"text": text, "formatting": formatting} if formatting else {"text": text}


# ── Date extractor ─────────────────────────────────────────────────────────────

def _extract_post_date(soup: BeautifulSoup) -> str:
    """Extract post date. Returns 'YYYYMMDD'. Falls back to today."""
    for sel in [".se_publishDate", ".blog_date", "span.se-date", "p.date", "[class*='date']"]:
        el = soup.select_one(sel)
        if el:
            m = re.search(r'(\d{4})[.\-/\s]+(\d{1,2})[.\-/\s]+(\d{1,2})', el.get_text(strip=True))
            if m:
                return f"{m.group(1)}{m.group(2).zfill(2)}{m.group(3).zfill(2)}"
    return datetime.now().strftime("%Y%m%d")


# ── Post parser + saver ────────────────────────────────────────────────────────

def _save_post(driver, url: str, category_dir: str) -> str | None:
    """
    Crawl a single post and save to category_dir/YYYYMMDD.json.
    Returns filename if saved, None if skipped (no paragraphs).
    """
    driver.get(url)
    WebDriverWait(driver, 10).until(
        lambda d: d.execute_script("return document.readyState") == "complete"
    )
    time.sleep(0.8)

    soup = BeautifulSoup(driver.page_source, "lxml")
    date_str = _extract_post_date(soup)

    title = ""
    for sel in [".se-title-text", "h3.se_textarea", ".se-module-text h3", "title"]:
        el = soup.select_one(sel)
        if el:
            title = el.get_text(strip=True)
            break

    content_root = (
        soup.select_one(".se-main-container") or
        soup.select_one(".se-component-content") or
        soup.select_one("#postViewArea") or
        soup
    )
    paragraphs = [p for p in (_para_to_json(p) for p in content_root.select(".se-text-paragraph")) if p]

    if not paragraphs:
        return None

    filename = f"{date_str}.json"
    filepath = os.path.join(category_dir, filename)
    if os.path.exists(filepath):
        idx = 2
        while os.path.exists(os.path.join(category_dir, f"{date_str}_{idx}.json")):
            idx += 1
        filename = f"{date_str}_{idx}.json"
        filepath = os.path.join(category_dir, filename)

    with open(filepath, "w", encoding="utf-8") as f:
        json.dump({"date": date_str, "title": title, "url": url, "paragraphs": paragraphs},
                  f, ensure_ascii=False, indent=2)

    return filename


# ── Category + URL collectors ──────────────────────────────────────────────────

def get_blog_categories(driver, blog_id: str) -> dict:
    """
    Return all categories from a blog's main page sidebar.
    Returns {category_name: category_no} dict.
    Uses from=postList links (left sidebar) — covers all categories.
    """
    driver.get(f"https://blog.naver.com/{blog_id}")
    WebDriverWait(driver, 10).until(
        lambda d: d.execute_script("return document.readyState") == "complete"
    )
    time.sleep(1)

    categories = {}
    try:
        driver.switch_to.frame(driver.find_element(By.ID, "mainFrame"))
        time.sleep(1)

        for link in driver.find_elements(By.CSS_SELECTOR, "a[href*='from=postList'][href*='categoryNo=']"):
            href = link.get_attribute("href") or ""
            m = re.search(r'categoryNo=(\d+)', href)
            if m and m.group(1) != "0":
                name = link.text.strip().replace("\u00a0", " ")
                if name:
                    categories[name] = m.group(1)

        driver.switch_to.default_content()
    except Exception:
        driver.switch_to.default_content()

    return categories


def get_category_post_links(driver, blog_id: str, category_name: str, category_no: str = None) -> list[dict]:
    """
    Navigate to a blog category, open the top list, switch to 30줄 보기,
    and collect up to 30 post links as [{"url": ..., "title": ...}].
    category_no를 직접 전달하면 get_blog_categories 재탐색을 건너뜀.
    """
    if not category_no:
        categories = get_blog_categories(driver, blog_id)
        category_no = categories.get(category_name)
        if not category_no:
            return [{"error": f"카테고리 '{category_name}' 를 찾을 수 없음. 가능한 카테고리: {list(categories.keys())}"}]

    try:
        # PostList URL로 직접 이동 — mainFrame iframe 없이 DOM 바로 접근
        driver.get(f"https://blog.naver.com/PostList.naver?blogId={blog_id}&from=postList&categoryNo={category_no}")
        WebDriverWait(driver, 10).until(
            lambda d: d.execute_script("return document.readyState") == "complete"
        )
        time.sleep(1)

        # Open 목록열기 if closed
        try:
            blind = driver.find_element(By.ID, "toplistSpanBlind")
            if blind.text.strip() == "목록열기":
                driver.find_element(By.CSS_SELECTOR, "a.btn_openlist").click()
                time.sleep(1)
        except NoSuchElementException:
            pass

        # Switch to 30줄 보기
        try:
            driver.find_element(By.ID, "listCountToggle").click()
            time.sleep(0.5)
            driver.find_element(By.CSS_SELECTOR, "#changeListCount a[data-value='30']").click()
            time.sleep(2)
        except (NoSuchElementException, TimeoutException):
            pass

        post_links = []
        for item in driver.find_elements(By.CSS_SELECTOR, "#toplistWrapper a._setTopListUrl")[:30]:
            href = item.get_attribute("href") or ""
            title = item.text.strip()
            if href and title:
                post_links.append({"url": href, "title": title})

        return post_links

    except Exception as e:
        return [{"error": str(e)}]


# ── Step 1: fetch all URLs ─────────────────────────────────────────────────────

def fetch_post_urls(driver, blog_id: str, categories: list[str] = None) -> dict:
    """
    Fetch post URLs from a blog, optionally filtered to specified categories.
    Saves to url_index/{blog_id}.json (merges with existing data).
    If categories is None, fetches all categories.
    Returns summary: {category_name: post_count}.
    """
    os.makedirs(URL_INDEX_DIR, exist_ok=True)

    all_categories = get_blog_categories(driver, blog_id)
    if not all_categories:
        return {"error": f"카테고리를 찾을 수 없음: {blog_id}"}

    target = {k: v for k, v in all_categories.items() if categories is None or k in categories}
    if not target:
        return {"error": f"카테고리 없음. 가능한 카테고리: {list(all_categories.keys())}"}

    # 기존 인덱스 로드 (있으면 merge)
    index_path = os.path.join(URL_INDEX_DIR, f"{blog_id}.json")
    existing = {}
    if os.path.exists(index_path):
        with open(index_path, encoding="utf-8") as f:
            existing = json.load(f).get("categories", {})

    result = dict(existing)
    for category_name, category_no in target.items():
        print(f"  [{category_name}] URL 수집 중...")
        links = get_category_post_links(driver, blog_id, category_name, category_no=category_no)
        valid = [l for l in links if "error" not in l]
        result[category_name] = valid
        print(f"  [{category_name}] {len(valid)}개 수집")

    index = {
        "blog_id": blog_id,
        "fetched_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "categories": result,
    }

    index_path = os.path.join(URL_INDEX_DIR, f"{blog_id}.json")
    with open(index_path, "w", encoding="utf-8") as f:
        json.dump(index, f, ensure_ascii=False, indent=2)

    summary = {cat: len(posts) for cat, posts in result.items()}
    return {"saved_to": index_path, "categories": summary}


# ── Step 2: create examples from index ────────────────────────────────────────

def create_examples_from_index(driver, blog_id: str, categories: list[str] = None) -> dict:
    """
    Load url_index/{blog_id}.json, crawl posts from specified categories,
    save each as examples/{category}/YYYYMMDD.json.
    If categories is None, process all categories in the index.
    """
    index_path = os.path.join(URL_INDEX_DIR, f"{blog_id}.json")
    if not os.path.exists(index_path):
        return {"error": f"url_index/{blog_id}.json 없음. 먼저 tool_fetch_post_urls 실행 필요."}

    with open(index_path, encoding="utf-8") as f:
        index = json.load(f)

    all_categories = index.get("categories", {})
    target = {k: v for k, v in all_categories.items() if categories is None or k in categories}

    if not target:
        return {"error": f"카테고리 없음. 가능한 카테고리: {list(all_categories.keys())}"}

    blog_dir = os.path.join(EXAMPLES_DIR, blog_id)
    os.makedirs(blog_dir, exist_ok=True)
    summary = {}

    for category_name, posts in target.items():
        print(f"\n[{category_name}] {len(posts)}개 포스트 크롤링...")
        category_dir = os.path.join(blog_dir, category_name)
        os.makedirs(category_dir, exist_ok=True)

        # 이미 저장된 URL 수집 (중복 크롤링 방지)
        saved_urls = set()
        for fname in os.listdir(category_dir):
            if fname.endswith(".json"):
                try:
                    with open(os.path.join(category_dir, fname), encoding="utf-8") as f:
                        saved_urls.add(json.load(f).get("url", ""))
                except Exception:
                    pass

        saved, skipped, errors = [], 0, 0
        for i, post in enumerate(posts):
            url = post.get("url", "")
            if not url:
                continue
            if url in saved_urls:
                print(f"  [{i+1}/{len(posts)}] 스킵 (이미 저장됨)")
                skipped += 1
                continue
            try:
                fname = _save_post(driver, url, category_dir)
                if fname:
                    saved.append(fname)
                    saved_urls.add(url)
                    print(f"  [{i+1}/{len(posts)}] 저장: {fname}")
                else:
                    skipped += 1
                    print(f"  [{i+1}/{len(posts)}] 스킵 (단락 없음)")
            except Exception as e:
                errors += 1
                print(f"  [{i+1}/{len(posts)}] 오류: {e}")

        summary[category_name] = {
            "saved": len(saved),
            "skipped": skipped,
            "errors": errors,
            "files": saved,
            "category_dir": category_dir,
        }

    return {"examples_dir": blog_dir, "categories": summary}

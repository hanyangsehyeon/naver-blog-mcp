"""
Naver Blog MCP Server (FastMCP)
Exposes tools: analyze_blog_style, get_style_profile, get_formatting_rules,
               get_blog_categories, get_category_posts,
               read_file, save_output, publish_to_naver
"""
import os, sys, json
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from mcp.server.fastmcp import FastMCP

from mcp_server.tools.file_tools import (
    convert_hwpx, read_file, save_output, load_output, get_formatting_rules
)
from mcp_server.tools.blog_analyzer import (
    fetch_post_urls, create_examples_from_index,
    get_blog_categories, get_category_post_links
)
from mcp_server.tools.publisher import publish_to_naver

mcp = FastMCP("naver-blog")

# Lazy-loaded Selenium driver (created on first use, reused across calls)
_driver = None
_logged_in = False

def _ensure_driver():
    global _driver
    if _driver is not None:
        try:
            _ = _driver.window_handles  # raises if session is dead
        except Exception:
            _driver = None
    if _driver is None:
        from tests.common import make_driver
        _driver = make_driver(headless=False)
    return _driver

def get_driver():
    """Driver without login — for public page access (URL collection, crawling)."""
    return _ensure_driver()

def get_driver_logged_in():
    """Driver with QR login — required for publishing."""
    global _logged_in
    driver = _ensure_driver()
    if not _logged_in:
        from tests.common import login_with_qr
        login_with_qr(driver)
        _logged_in = True
    return driver


@mcp.tool()
def tool_fetch_post_urls(blog_id: str, categories: list[str] = None) -> str:
    """Fetch post URLs from a blog and save to url_index/{blog_id}.json.
    If categories is specified, fetches only those categories (merges with existing index).
    If categories is None, fetches all categories.
    Run tool_get_blog_categories first to see available category names."""
    driver = get_driver()
    result = fetch_post_urls(driver, blog_id, categories)
    return json.dumps(result, ensure_ascii=False, indent=2)


@mcp.tool()
def tool_create_examples(blog_id: str, categories: list[str] = None) -> str:
    """Load url_index/{blog_id}.json, crawl posts from specified categories,
    save each as examples/{category}/YYYYMMDD.json for few-shot prompting.
    If categories is None, process all categories in the index."""
    driver = get_driver()
    result = create_examples_from_index(driver, blog_id, categories)
    return json.dumps(result, ensure_ascii=False, indent=2)


@mcp.tool()
def tool_get_formatting_rules() -> str:
    """Return the user's formatting_rules.json — priority rules for when to apply
    highlight / text_color / bold."""
    return json.dumps(get_formatting_rules(), ensure_ascii=False, indent=2)


@mcp.tool()
def tool_convert_hwpx(filename: str) -> str:
    """Convert a .hwpx file from input/ to .txt in drafts/.
    filename: e.g. '글감.hwpx'
    Returns the saved txt file path."""
    path = convert_hwpx(filename)
    return json.dumps({"saved_to": path})


@mcp.tool()
def tool_read_file(filename: str) -> str:
    """Read a .txt file from the drafts/ directory."""
    return read_file(filename)


@mcp.tool()
def tool_save_output(filename: str, content: dict) -> str:
    """Save transformed paragraph JSON to output/ for debugging."""
    path = save_output(filename, content)
    return json.dumps({"saved_to": path})


@mcp.tool()
def tool_get_blog_categories(blog_id: str) -> str:
    """Return all categories of a Naver blog as {name: categoryNo} dict.
    Use this before tool_get_category_posts to discover available category names."""
    driver = get_driver()
    result = get_blog_categories(driver, blog_id)
    return json.dumps(result, ensure_ascii=False, indent=2)


@mcp.tool()
def tool_get_category_posts(blog_id: str, category_name: str) -> str:
    """Navigate to a blog category via the main page UI, open the top list,
    switch to 30줄 보기, and return up to 30 post links.
    Returns list of {url, title}.
    If category not found, returns error with list of available categories."""
    driver = get_driver()
    result = get_category_post_links(driver, blog_id, category_name)
    return json.dumps(result, ensure_ascii=False, indent=2)


@mcp.tool()
def tool_publish_to_naver(blog_id: str, title: str, paragraphs: list, from_output: str = "") -> str:
    """Open Naver Blog editor for blog_id and save as draft.
    IMPORTANT: Always confirm blog_id with the user before calling this tool.
    Does NOT publish — user reviews and publishes manually.
    If from_output is set (output/ filename), load title+paragraphs from that file instead of inline args.
    Each paragraph: {text: str, formatting: [{type: bold|highlight|text_color, start: int, end: int, color?: str}]}"""
    if from_output:
        data = load_output(from_output)
        title = data.get("title", title)
        paragraphs = data.get("paragraphs", paragraphs)
    driver = get_driver_logged_in()
    result = publish_to_naver(driver, blog_id=blog_id, title=title, paragraphs=paragraphs)
    return json.dumps(result, ensure_ascii=False, indent=2)


if __name__ == "__main__":
    mcp.run()

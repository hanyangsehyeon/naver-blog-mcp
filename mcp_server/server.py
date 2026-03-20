"""
Naver Blog MCP Server
Exposes tools: analyze_blog_style, get_style_profile, get_formatting_rules,
               read_file, save_output, publish_to_naver
"""
import os, sys, json
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp import types

from mcp_server.tools.file_tools import (
    read_file, save_output, get_style_profile, get_formatting_rules
)
from mcp_server.tools.blog_analyzer import analyze_blog_style
from mcp_server.tools.publisher import publish_to_naver

# Lazy-loaded Selenium driver (created on first use, reused across calls)
_driver = None

def get_driver():
    global _driver
    if _driver is None:
        from tests.common import make_driver, login_with_qr
        _driver = make_driver(headless=False)
        login_with_qr(_driver)
    return _driver


app = Server("naver-blog")


@app.list_tools()
async def list_tools() -> list[types.Tool]:
    return [
        types.Tool(
            name="analyze_blog_style",
            description=(
                "Crawl the user's Naver blog to learn their formatting style. "
                "Extracts bold/highlight/text-color examples and saves style_profile.json. "
                "Run this once before publishing to capture color preferences."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "blog_id": {"type": "string", "description": "Naver blog ID to analyze"},
                    "post_count": {"type": "integer", "description": "Number of recent posts to crawl (default 10)", "default": 10},
                },
                "required": ["blog_id"],
            },
        ),
        types.Tool(
            name="get_style_profile",
            description="Return contents of style_profile.json (null if not yet generated).",
            inputSchema={"type": "object", "properties": {}},
        ),
        types.Tool(
            name="get_formatting_rules",
            description=(
                "Return the user's formatting_rules.json — priority rules for when to apply "
                "highlight / text_color / bold."
            ),
            inputSchema={"type": "object", "properties": {}},
        ),
        types.Tool(
            name="read_file",
            description="Read a raw text file from the input/ directory.",
            inputSchema={
                "type": "object",
                "properties": {
                    "filename": {"type": "string", "description": "Filename inside input/"},
                },
                "required": ["filename"],
            },
        ),
        types.Tool(
            name="save_output",
            description="Save transformed paragraph JSON to output/ for debugging.",
            inputSchema={
                "type": "object",
                "properties": {
                    "filename": {"type": "string"},
                    "content": {"type": "object"},
                },
                "required": ["filename", "content"],
            },
        ),
        types.Tool(
            name="publish_to_naver",
            description=(
                "Open Naver Blog editor, input title + formatted paragraphs, and save as draft. "
                "Does NOT publish — user reviews and publishes manually. "
                "Each paragraph may include formatting: bold, highlight (bg color), text_color."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "blog_id": {"type": "string"},
                    "title": {"type": "string"},
                    "paragraphs": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "text": {"type": "string"},
                                "formatting": {
                                    "type": "array",
                                    "items": {
                                        "type": "object",
                                        "properties": {
                                            "type": {"type": "string", "enum": ["bold", "highlight", "text_color"]},
                                            "start": {"type": "integer"},
                                            "end": {"type": "integer"},
                                            "color": {"type": "string"},
                                        },
                                        "required": ["type", "start", "end"],
                                    },
                                },
                            },
                            "required": ["text"],
                        },
                    },
                },
                "required": ["blog_id", "title", "paragraphs"],
            },
        ),
    ]


@app.call_tool()
async def call_tool(name: str, arguments: dict) -> list[types.TextContent]:
    def ok(data) -> list[types.TextContent]:
        return [types.TextContent(type="text", text=json.dumps(data, ensure_ascii=False, indent=2))]

    def err(msg: str) -> list[types.TextContent]:
        return [types.TextContent(type="text", text=json.dumps({"error": msg}, ensure_ascii=False))]

    try:
        if name == "get_style_profile":
            return ok(get_style_profile())

        elif name == "get_formatting_rules":
            return ok(get_formatting_rules())

        elif name == "read_file":
            return ok({"content": read_file(arguments["filename"])})

        elif name == "save_output":
            path = save_output(arguments["filename"], arguments["content"])
            return ok({"saved_to": path})

        elif name == "analyze_blog_style":
            driver = get_driver()
            profile = analyze_blog_style(
                driver,
                blog_id=arguments["blog_id"],
                post_count=arguments.get("post_count", 10),
            )
            return ok(profile)

        elif name == "publish_to_naver":
            driver = get_driver()
            result = publish_to_naver(
                driver,
                blog_id=arguments["blog_id"],
                title=arguments["title"],
                paragraphs=arguments["paragraphs"],
            )
            return ok(result)

        else:
            return err(f"unknown tool: {name}")

    except Exception as e:
        return err(str(e))


if __name__ == "__main__":
    import asyncio
    asyncio.run(stdio_server(app))

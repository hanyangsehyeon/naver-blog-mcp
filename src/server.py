# -*- coding: utf-8 -*-
from mcp.server.fastmcp import FastMCP

from src.crawler.naver_crawler import fetch_raw_posts
from src.tools.converter import convert_to_blog_post
from src.tools.file_io import read_file, save_file
from src.tools.learner import learn_blog_style
from src.tools.publisher import publish_to_naver

mcp = FastMCP("naver-blog")

mcp.tool()(fetch_raw_posts)
mcp.tool()(convert_to_blog_post)
mcp.tool()(read_file)
mcp.tool()(save_file)
mcp.tool()(learn_blog_style)
mcp.tool()(publish_to_naver)

if __name__ == "__main__":
    mcp.run()

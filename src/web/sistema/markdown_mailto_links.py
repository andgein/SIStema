from markdown2 import Markdown
import re


def enable_mailto_links_in_markdown():
    # Hack to make mailto-links safe in markdown engine
    Markdown._safe_protocols = re.compile(r'(https?|ftp|mailto):', re.I)

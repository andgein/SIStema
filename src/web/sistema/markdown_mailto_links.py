from markdown2 import Markdown
import re

# Hack to make mailto-links safe in markdown engine
Markdown._safe_protocols = re.compile(r'(https?|ftp|mailto):', re.I)

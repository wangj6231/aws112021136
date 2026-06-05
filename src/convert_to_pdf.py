import markdown
from playwright.sync_api import sync_playwright
import os

md_path = r"C:\Users\milo9\Desktop\aws112021136\src\Combined_AWS_TDCS_Report_Group_112021136.md"
html_path = r"C:\Users\milo9\Desktop\aws112021136\src\report_temp.html"
pdf_path = r"C:\Users\milo9\Desktop\aws112021136\src\Combined_AWS_TDCS_Report_Group_112021136.pdf"

with open(md_path, 'r', encoding='utf-8') as f:
    text = f.read()

# Custom extension to support Mermaid blocks from markdown to div class="mermaid"
html_body = markdown.markdown(text, extensions=['tables', 'fenced_code'])
html_body = html_body.replace('<pre><code class="language-mermaid">', '<div class="mermaid">')
html_body = html_body.replace('</code></pre>', '</div>')

html_content = f"""
<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<style>
    body {{
        font-family: "Microsoft JhengHei", "PingFang TC", sans-serif;
        line-height: 1.6;
        padding: 2em;
        color: #333;
    }}
    h1, h2, h3 {{
        color: #2c3e50;
        border-bottom: 1px solid #eee;
        padding-bottom: 0.3em;
    }}
    img {{
        max-width: 100%;
        height: auto;
        display: block;
        margin: 1em auto;
        border: 1px solid #ddd;
        border-radius: 4px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }}
    pre {{
        background-color: #f4f4f4;
        padding: 1em;
        border-radius: 4px;
        overflow-x: auto;
    }}
    code {{
        font-family: Consolas, monospace;
        background-color: #f4f4f4;
        padding: 0.2em 0.4em;
        border-radius: 3px;
    }}
    table {{
        border-collapse: collapse;
        width: 100%;
        margin-bottom: 1em;
    }}
    table, th, td {{
        border: 1px solid #ddd;
    }}
    th, td {{
        padding: 8px;
        text-align: left;
    }}
    th {{
        background-color: #f2f2f2;
    }}
    .mermaid {{
        text-align: center;
        margin: 2em 0;
    }}
</style>
<script src="https://cdn.jsdelivr.net/npm/mermaid/dist/mermaid.min.js"></script>
<script>mermaid.initialize({{startOnLoad:true}});</script>
</head>
<body>
{html_body}
</body>
</html>
"""

with open(html_path, 'w', encoding='utf-8') as f:
    f.write(html_content)

def generate_pdf():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        file_url = f"file:///{html_path.replace(chr(92), '/')}"
        print(f"Loading HTML: {file_url}")
        page.goto(file_url, wait_until="networkidle") 
        # Wait a bit more to ensure mermaid renders completely
        page.wait_for_timeout(3000)
        page.emulate_media(media="screen")
        page.pdf(path=pdf_path, format="A4", margin={"top": "20mm", "bottom": "20mm", "left": "20mm", "right": "20mm"})
        browser.close()

generate_pdf()
print(f"PDF successfully generated at: {pdf_path}")

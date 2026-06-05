import os
import re

md_path = r"C:\Users\milo9\Desktop\aws112021136\src\Combined_AWS_TDCS_Report_Group_112021136.md"

with open(md_path, 'r', encoding='utf-8') as f:
    content = f.read()

# Replace absolute file paths with relative ones
content = content.replace("file:///C:/Users/milo9/Desktop/aws112021136/src/", "./")
# For the Cost Explorer image specifically, which was URL encoded
content = content.replace("%E8%9E%A2%E5%B9%95%E6%93%B7%E5%8F%96%E7%95%AB%E9%9D%A2", "螢幕擷取畫面")

# Replace Google Map placeholder with the actual image
map_placeholder = "> *(請在此處貼上GoogleMap截圖，標示出永康交流道與4個匝道代碼的位置)*"
map_image_md = "> ![Google Map 永康交流道](./map_screenshot.png)"
if map_placeholder in content:
    content = content.replace(map_placeholder, map_image_md)

with open(md_path, 'w', encoding='utf-8') as f:
    f.write(content)

print("Markdown updated with relative paths and map image.")

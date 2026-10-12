import re
import sys
import io

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

with open("d:/Coding/Dự án FTS/WebFTS v4/FTS Server/scenario/_gen_kb5_1hour.py", "r", encoding="utf-8") as f:
    content = f.read()

# Tăng giãn cách lên 220s để đảm bảo >9NM sau CADAS
content = content.replace('ARR_SPACING_S = 180', 'ARR_SPACING_S = 220')
content = content.replace('DEP_SPACING_S = 180', 'DEP_SPACING_S = 220')

with open("d:/Coding/Dự án FTS/WebFTS v4/FTS Server/scenario/_gen_kb5_1hour.py", "w", encoding="utf-8") as f:
    f.write(content)

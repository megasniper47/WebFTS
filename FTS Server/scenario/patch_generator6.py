import re
import sys
import io

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

with open("d:/Coding/Dự án FTS/WebFTS v4/FTS Server/scenario/_gen_kb5_1hour.py", "r", encoding="utf-8") as f:
    content = f.read()

# Đổi lại giãn cách 180s theo yêu cầu
content = content.replace('ARR_SPACING_S = 220', 'ARR_SPACING_S = 180')
content = content.replace('DEP_SPACING_S = 220', 'DEP_SPACING_S = 180')

with open("d:/Coding/Dự án FTS/WebFTS v4/FTS Server/scenario/_gen_kb5_1hour.py", "w", encoding="utf-8") as f:
    f.write(content)

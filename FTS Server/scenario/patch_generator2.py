import re
import sys
import io

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

with open("d:/Coding/Dự án FTS/WebFTS v4/FTS Server/scenario/_gen_kb5_1hour.py", "r", encoding="utf-8") as f:
    content = f.read()

# Replace random.choice for star selection with weighted choices
old_star_choice = 'star = random.choice(list(STAR_IAF.keys()))'
new_star_choice = """# Tỉ lệ hướng (chuẩn hoá từ 30/30/15/15 = 90%):
        # Bắc (HUE, CAHEO): 30
        # Nam (KUMUN, SADIN, VILOT): 30
        # Đông (BUNTA): 15
        # Tây (LATOM, PAPRA): 15
        star_weights = {
            "HUE": 15, "CAHEO": 15,        # Bắc
            "KUMUN": 10, "SADIN": 10, "VILOT": 10, # Nam
            "BUNTA": 15,                   # Đông
            "LATOM": 7.5, "PAPRA": 7.5     # Tây
        }
        star_keys = list(star_weights.keys())
        star_probs = list(star_weights.values())
        star = random.choices(star_keys, weights=star_probs, k=1)[0]"""

content = content.replace(old_star_choice, new_star_choice)

# Enable backup output again just to be safe, or just keep it outputting to the same dir
# I will let it output to the backup directory by leaving OUT_DIR as it is.

with open("d:/Coding/Dự án FTS/WebFTS v4/FTS Server/scenario/_gen_kb5_1hour.py", "w", encoding="utf-8") as f:
    f.write(content)

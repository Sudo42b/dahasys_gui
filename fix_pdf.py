import re

with open("minias_app.py", "r", encoding="utf-8") as f:
    content = f.read()

# Add BACKGROUND to info_table
info_style = """                        ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
                        ("BACKGROUND", (0, 0), (0, 0), colors.Color(0.9, 0.9, 0.9)), # Probe Model
                        ("BACKGROUND", (2, 0), (2, 0), colors.Color(0.9, 0.9, 0.9)), # Code
                        ("BACKGROUND", (4, 0), (4, 0), colors.Color(0.9, 0.9, 0.9)), # Serial
"""
content = content.replace('("GRID", (0, 0), (-1, -1), 0.5, colors.grey),', info_style)

# axis_table already has: ("BACKGROUND", (0, 0), (-1, 0), colors.Color(0.95, 0.95, 0.95)),
# Wait, axis_table row 0 contains "Direction", "Y-", "", "X+", "", "Y+", "", "X-", ""
# I need to target specifically the labels. The current style applies to the whole row 0!
# The request says: "Target labels: Direction, Y-, X+, Y+, X-"

# Let's use a Python script to do the replacement more carefully.

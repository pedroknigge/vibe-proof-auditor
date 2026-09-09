import re

with open("/Users/pedroknigge/Desktop/Quill/vibe-proof-audit-report.md", "r") as f:
    content = f.read()

# Fix gates table
content = content.replace("1. Critical security", "Critical security")
content = content.replace("2. Testing", "Testing")
content = content.replace("3. Error handling", "Error handling")
content = content.replace("4. Environment isolation", "Environment isolation")

# Fix math
content = content.replace("| 2. Comprehension | 5 | 2 | 0 | 0 | 0 | no | 8 |", "| 2. Comprehension | 5 | 2 | 0 | 0 | 0 | no | 9 |")
content = content.replace("| 3. Testing | 1 | 2 | 5 | 0 | 0 | no | 2 |", "| 3. Testing | 1 | 2 | 5 | 0 | 0 | no | 3 |")
content = content.replace("| 9. Process / environments | 1 | 1 | 2 | 0 | 2 | no | 3 |", "| 9. Process / environments | 1 | 1 | 2 | 0 | 2 | no | 4 |")

content = content.replace("| 2. Comprehension | 8 |", "| 2. Comprehension | 9 |")
content = content.replace("| 3. Testing | 2 |", "| 3. Testing | 3 |")
content = content.replace("| 9. Process / environments | 3 |", "| 9. Process / environments | 4 |")

content = content.replace("**Overall Score:** 7.5 / 10", "**Overall Score:** 8.2 / 10")
content = content.replace("**Stage note:** Production", "**Stage note:** Do not ship as-is. Harden first.")

with open("/Users/pedroknigge/Desktop/Quill/vibe-proof-audit-report.md", "w") as f:
    f.write(content)


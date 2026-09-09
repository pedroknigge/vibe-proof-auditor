import re

with open("/Users/pedroknigge/Desktop/Quill/vibe-proof-audit-report.md", "r") as f:
    content = f.read()

content = content.replace("**Status:** NEEDS HARDENING", "**Status:** BLOCKED FOR PRODUCTION")
content = content.replace("**Stage note:** Do not ship as-is. Harden first.", "**Stage note:** Not expected. Do not ship.")

with open("/Users/pedroknigge/Desktop/Quill/vibe-proof-audit-report.md", "w") as f:
    f.write(content)


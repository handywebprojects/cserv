###################################################

from utils.file import *
import re

###################################################

confightml = read_string_from_file("firebase/config.html", "")

config = {}
for line in confightml.split("\n"):
    s = re.search(r"""\s+(\w*):[^"]*"([^"]*)""", line)
    if s:
        key = s.group(1)
        value = s.group(2)
        config[key] = value
    write_json_to_file("firebase/config.json", config)

###################################################
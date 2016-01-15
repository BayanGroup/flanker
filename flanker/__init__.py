import re

# re.ASCII_FLAG alternative for both python 2 and python 3
try:
    RE_ASCII_FLAG = re.ASCII
except AttributeError:
    RE_ASCII_FLAG = 0 #  python 2

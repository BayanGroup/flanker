import re

try:
    ASCII_FLAG = re.ASCII
except AttributeError:
    ASCII_FLAG = 0
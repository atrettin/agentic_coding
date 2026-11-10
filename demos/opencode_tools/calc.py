import re
import sys

expression = sys.argv[1]
if not re.fullmatch(r"[\d\s+\-*/().]+", expression):  # only arithmetic: never eval text from a model unchecked
    print("error: only numbers and + - * / ( ) are allowed")
else:
    print(eval(expression))

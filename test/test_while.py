from yapypy.utils.easy_debug import easy_debug

code = r"""
i= 0
while i<10 and i!=5:
    print(i)
    i+=1
"""

easy_debug(code, True)

from yapypy.utils.easy_debug import easy_debug

code = r"""
lfkdsk : int = 1111111
assert lfkdsk == 1111111
d : int = 2000 if lfkdsk == 1111111 else 3000
assert d == 2000
a = [1, 3, 5]
a[1] : int = 1000
assert a[1] == 1000
def fun(x : int):
    return x
assert fun(100) == 100
s : dict = dict()
assert s is not None
"""

if __name__ == '__main__':
    easy_debug(code, True)

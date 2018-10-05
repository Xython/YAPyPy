from yapypy.utils.easy_debug import easy_debug

code = r'''
def f(*args, **kwargs):
    print(args, kwargs)

f(1,2,c=3,d=4)

'''

easy_debug(code, True)
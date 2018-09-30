from kizmi.extended_python.parser import parse
mod = parse(r"""    

class G:
    @property
    def a(self):
        return "hello pypy!"

def f():
    print(G().a)
    
def g(x=1):
    print(x + 2)

f()
g(x=1)
""").result

code = compile(mod, "test", "exec")
exec(code)

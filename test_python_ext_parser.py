from kizmi.extended_python.parser import parse
mod = parse(r"""    
class G:
    @property
    def a(self):
        return "hello pypy!"

def f():
    print(G().a)

f()
""").result

code = compile(mod, "test", "exec")
exec(code)

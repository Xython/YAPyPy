from kizmi.extended_python.parser import parse
mod = parse(r"""
print(1)
""").result

code = compile(mod, "test", "exec")
exec(code)

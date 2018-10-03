# Code Object

下文中，若Python指Python解释器，如无特别注明，指的是CPython 3.6

Python中，一个函数`f`的code object可以从`f.__code__`得到

```pycon
>>> def f(): pass
...
>>> f.__code__
<code object f at 0x7f0000000000, file "<stdin>", line 1>
```

用[dis.show_code](https://docs.python.org/3.6/library/dis.html#dis.show_code)可以显示code object的详细信息

```pycon
>>> show_code(f)
Name:              f
Filename:          <stdin>
Argument count:    0
Kw-only arguments: 0
Number of locals:  0
Stack size:        1
Flags:             OPTIMIZED, NEWLOCALS, NOFREE
Constants:
   0: None
```

一个函数的code object，Name就是函数名。如果是lambda，Name是`<lambda>`

```pycon
>>> show_code(lambda: None)
Name:              <lambda>
Filename:          <stdin>
Argument count:    0
Kw-only arguments: 0
Number of locals:  0
Stack size:        1
Flags:             OPTIMIZED, NEWLOCALS, NOFREE
Constants:
   0: None
```

Filename就是函数定义所在的文件名，如果是在Shell中输入的，就会是`<stdin>`

而Python代码会编译成字节码，可以通过[dis.dis](https://docs.python.org/3.6/library/dis.html#dis.dis)查看

```pycon
>>> dis(f)
  1           0 LOAD_CONST               0 (None)
              2 RETURN_VALUE
```

Constants是常量表，[LOAD_CONST](https://docs.python.org/3.6/library/dis.html#opcode-LOAD_CONST) 0就是取出常量表中第0个元素。

## 修改

code object是不能修改的

```pycon
>>> f.__code__.co_name = "x"
Traceback (most recent call last):
  File "<stdin>", line 1, in <module>
AttributeError: readonly attribute
```

可以建一个新的替代，比如换一个不同的常量表

```pycon
>>> from types import CodeType
>>> def replace(obj, **kwargs):
...     args = ("argcount", "kwonlyargcount", "nlocals", "stacksize", "flags", "code", "consts", "names", "varnames", "filename" ,"name", "firstlineno", "lnotab", "freevars", "cellvars")
...     return CodeType(*(kwargs.get(a, getattr(obj, "co_"+a)) for a in args))
...
>>> f.__code__ = replace(f.__code__, consts=(1,))
>>> show_code(f)
Name:              f
Filename:          <stdin>
Argument count:    0
Kw-only arguments: 0
Number of locals:  0
Stack size:        1
Flags:             OPTIMIZED, NEWLOCALS, NOFREE
Constants:
   0: 1
>>> f()
1
```

## 用途

Code object不只用于普通函数，所有Python代码都会有Code object，不同的用途可能会需要设置不同的Flag

嵌套函数要有Flag NESTED

```pycon
>>> def f():
...     def g(): pass
...     show_code(g)
...
>>> f()
Name:              g
Filename:          <stdin>
Argument count:    0
Kw-only arguments: 0
Number of locals:  0
Stack size:        1
Flags:             OPTIMIZED, NEWLOCALS, NESTED, NOFREE
Constants:
   0: None
```

Generator要有Flag GENERATOR

```pycon
>>> def g(): yield
...
>>> show_code(f)
Name:              f
Filename:          <stdin>
Argument count:    0
Kw-only arguments: 0
Number of locals:  0
Stack size:        1
Flags:             OPTIMIZED, NEWLOCALS, GENERATOR, NOFREE
Constants:
   0: None
```

Coroutine要有Flag COROUTINE

```pycon
>>> async def c(): pass
...
>>> show_code(c)
Name:              c
Filename:          <stdin>
Argument count:    0
Kw-only arguments: 0
Number of locals:  0
Stack size:        1
Flags:             OPTIMIZED, NEWLOCALS, NOFREE, COROUTINE
Constants:
   0: None
```

[PEP-492](https://www.python.org/dev/peps/pep-0492/) Iterable Coroutine要有Flag ITERABLE_COROUTINE

```pycon
>>> from types import coroutine
>>> @coroutine
... def ic(): yield
...
>>> show_code(ic)
Name:              ic
Filename:          <stdin>
Argument count:    0
Kw-only arguments: 0
Number of locals:  0
Stack size:        1
Flags:             OPTIMIZED, NEWLOCALS, GENERATOR, NOFREE, ITERABLE_COROUTINE
Constants:
   0: None
```

[PEP-535](https://www.python.org/dev/peps/pep-0525/) Async Generator要有Flag ASYNC_GENERATOR

```pycon
>>> async def ag(): yield
...
>>> show_code(ag)
Name:              ag
Filename:          <stdin>
Argument count:    0
Kw-only arguments: 0
Number of locals:  0
Stack size:        1
Flags:             OPTIMIZED, NEWLOCALS, NOFREE, ASYNC_GENERATOR
Constants:
   0: None
```

注意Class是没有Flag OPTIMIZED和NEWLOCALS的

```pycon
>>> code = compile("class A: x = 1", "<stdin>", "exec")
>>> show_code(code.co_consts[0])
Name:              A
Filename:          <stdin>
Argument count:    0
Kw-only arguments: 0
Number of locals:  0
Stack size:        1
Flags:             NOFREE
Constants:
   0: 'A'
   1: 1
   2: None
Names:
   0: __name__
   1: __module__
   2: __qualname__
   3: x
>>> d = {}
>>> exec(code.co_consts[0], globals(), d)
>>> A = type('A', (), d)
>>> A.x
1
```
Module也是没有Flag OPTIMIZED和NEWLOCALS的

```pycon
>>> code = compile("x = 1", "<stdin>", "exec")
>>> show_code(code)
Name:              <module>
Filename:          <stdin>
Argument count:    0
Kw-only arguments: 0
Number of locals:  0
Stack size:        1
Flags:             NOFREE
Constants:
   0: 1
   1: None
Names:
   0: x
>>> from types import ModuleType
>>> mod = ModuleType("example")
>>> exec(code, mod.__dict__, mod.__dict__)
>>> import sys
>>> sys.modules["example"] = mod
>>> import example
>>> example.x
1
```

### NEWLOCALS

设置了NEWLOCALS，每次都会创建一个新的locals

```pycon
>>> code = compile("x = 1", "<stdin>", "exec")
>>> d = {}
>>> exec(code, globals(), d)
>>> d
{'x': 1}
>>> code = replace(code, flags = code.co_flags|2)
>>> show_code(code)
Name:              <module>
Filename:          <stdin>
Argument count:    0
Kw-only arguments: 0
Number of locals:  0
Stack size:        1
Flags:             NEWLOCALS, NOFREE
Constants:
   0: 1
   1: None
Names:
   0: x
>>> d = {}
>>> exec(code, globals(), d)
>>> d
{}
```

可以看到不会影响传入的locals

## 变量

### 全局变量

主要有三个和全局变量相关的Opcode，[LOAD_GLOBAL](https://docs.python.org/3.6/library/dis.html#opcode-LOAD_GLOBAL)，[STORE_GLOBAL](https://docs.python.org/3.6/library/dis.html#opcode-STORE_GLOBAL)和[DELETE_GLOBAL](https://docs.python.org/3.6/library/dis.html#opcode-DELETE_GLOBAL)，举个例子

```pycon
>>> def f():
...     def g():
...         global x
...         x = 1
...     show_code(g)
...     dis(g)
...
>>> f()
Name:              g
Filename:          <stdin>
Argument count:    0
Kw-only arguments: 0
Number of locals:  0
Stack size:        1
Flags:             OPTIMIZED, NEWLOCALS, NESTED, NOFREE
Constants:
   0: None
   1: 1
Names:
   0: x
  4           0 LOAD_CONST               1 (1)
              2 STORE_GLOBAL             0 (x)
              4 LOAD_CONST               0 (None)
              6 RETURN_VALUE
```

### 局部变量

主要有三个和局部变量相关的Opcode，[LOAD_FAST](https://docs.python.org/3.6/library/dis.html#opcode-LOAD_FAST)，[STORE_FAST](https://docs.python.org/3.6/library/dis.html#opcode-STORE_FAST)和[DELETE_FAST](https://docs.python.org/3.6/library/dis.html#opcode-DELETE_FAST)，举个例子

```pycon
>>> def f():
...     def g():
...         x = 1
...     show_code(g)
...     dis(g)
...
>>> f()
Name:              g
Filename:          <stdin>
Argument count:    0
Kw-only arguments: 0
Number of locals:  1
Stack size:        1
Flags:             OPTIMIZED, NEWLOCALS, NESTED, NOFREE
Constants:
   0: None
   1: 1
Variable names:
   0: x
  3           0 LOAD_CONST               1 (1)
              2 STORE_FAST               0 (x)
              4 LOAD_CONST               0 (None)
              6 RETURN_VALUE
```

### 参数

所有的参数都是局部变量，可以看到Number of locals为1。而Argument count是参数个数

```pycon
>>> def f1(a): pass
...
>>> show_code(f1)
Name:              f1
Filename:          <stdin>
Argument count:    1
Kw-only arguments: 0
Number of locals:  1
Stack size:        1
Flags:             OPTIMIZED, NEWLOCALS, NOFREE
Constants:
   0: None
Variable names:
   0: a
```

Kw-only arguments是只接受keyword形式的参数个数

```pycon
>>> def f2(a, *, b): pass
...
>>> show_code(f2)
Name:              f2
Filename:          <stdin>
Argument count:    1
Kw-only arguments: 1
Number of locals:  2
Stack size:        1
Flags:             OPTIMIZED, NEWLOCALS, NOFREE
Constants:
   0: None
Variable names:
   0: a
   1: b
```

Flag VARARGS

```pycon
>>> def f3(*args): pass
...
>>> show_code(f3)
Name:              f3
Filename:          <stdin>
Argument count:    0
Kw-only arguments: 0
Number of locals:  1
Stack size:        1
Flags:             OPTIMIZED, NEWLOCALS, VARARGS, NOFREE
Constants:
   0: None
Variable names:
   0: args
```

Flag VARKEYWORDS

```pycon
>>> def f4(**kwargs): pass
...
>>> show_code(f4)
Name:              f4
Filename:          <stdin>
Argument count:    0
Kw-only arguments: 0
Number of locals:  1
Stack size:        1
Flags:             OPTIMIZED, NEWLOCALS, VARKEYWORDS, NOFREE
Constants:
   0: None
Variable names:
   0: kwargs
```

Variable names的顺序

```pycon
>>> def f5(a, *b, c, **d): pass
...
>>> show_code(f5)
Name:              f5
Filename:          <stdin>
Argument count:    1
Kw-only arguments: 1
Number of locals:  4
Stack size:        1
Flags:             OPTIMIZED, NEWLOCALS, VARARGS, VARKEYWORDS, NOFREE
Constants:
   0: None
Variable names:
   0: a
   1: c
   2: b
   3: d
```

### Free/Cell

主要有三个和Free/Cell变量相关的Opcode，[LOAD_DEREF](https://docs.python.org/3.6/library/dis.html#opcode-LOAD_DEREF)，[STORE_DEREF](https://docs.python.org/3.6/library/dis.html#opcode-STORE_DEREF)和[DELETE_DEREF](https://docs.python.org/3.6/library/dis.html#opcode-DELETE_DEREF)，举个例子

```pycon
>>> def f():
...     x = 1
...     def g():
...         return x
...     show_code(g)
...     dis(g)
...
>>> f()
Name:              g
Filename:          <stdin>
Argument count:    0
Kw-only arguments: 0
Number of locals:  0
Stack size:        1
Flags:             OPTIMIZED, NEWLOCALS, NESTED
Constants:
   0: None
Free variables:
   0: x
  4           0 LOAD_DEREF               0 (x)
              2 RETURN_VALUE
```

而上层作用域中的局部变量变成了Cell变量，而在[MAKE_FUNCTION](https://docs.python.org/3.6/library/dis.html#opcode-MAKE_FUNCTION)之前需要先用[LOAD_CLOSURE](https://docs.python.org/3.6/library/dis.html#opcode-LOAD_CLOSURE),[BUILD_TUPLE](https://docs.python.org/3.6/library/dis.html#opcode-BUILD_TUPLE)生成一个tuple

```pycon
>>> show_code(f)
Name:              f
Filename:          <stdin>
Argument count:    0
Kw-only arguments: 0
Number of locals:  1
Stack size:        3
Flags:             OPTIMIZED, NEWLOCALS
Constants:
   0: None
   1: 1
   2: <code object g at 0x7f0000001000, file "<stdin>", line 3>
   3: 'f.<locals>.g'
Names:
   0: show_code
   1: dis
Variable names:
   0: g
Cell variables:
   0: x
  2           0 LOAD_CONST               1 (1)
              2 STORE_DEREF              0 (x)

  3           4 LOAD_CLOSURE             0 (x)
              6 BUILD_TUPLE              1
              8 LOAD_CONST               2 (<code object g at 0x7f0000001000, file "<stdin>", line 3>)
             10 LOAD_CONST               3 ('f.<locals>.g')
             12 MAKE_FUNCTION            8
             14 STORE_FAST               0 (g)

  5          16 LOAD_GLOBAL              0 (show_code)
             18 LOAD_FAST                0 (g)
             20 CALL_FUNCTION            1
             22 POP_TOP

  6          24 LOAD_GLOBAL              1 (dis)
             26 LOAD_FAST                0 (g)
             28 CALL_FUNCTION            1
             30 POP_TOP
             32 LOAD_CONST               0 (None)
             34 RETURN_VALUE
```

另外，有了Free或Cell变量，就不能有Flag NOFREE了


### OPTIMIZED

有Flag OPTIMIZED的code object在编译的时候就已经确定了每个变量的作用域。而对于Module来说，globals和locals是相同的，并且locals的个数并不能在编译期确定，于是不能设置Flag OPTIMIZED，操作变量用[LOAD_NAME](https://docs.python.org/3.6/library/dis.html#opcode-LOAD_NAME)，[STORE_NAME](https://docs.python.org/3.6/library/dis.html#opcode-STORE_NAME)和[DELETE_NAME](https://docs.python.org/3.6/library/dis.html#opcode-DELETE_NAME)。这三个Opcode是在运行期确定变量的作用域。比如

```pycon
>>> code = compile("x = 1", "<stdin>", "exec")
>>> show_code(code)
Name:              <module>
Filename:          <stdin>
Argument count:    0
Kw-only arguments: 0
Number of locals:  0
Stack size:        1
Flags:             NOFREE
Constants:
   0: 1
   1: None
Names:
   0: x
>>> dis(code)
  1           0 LOAD_CONST               0 (1)
              2 STORE_NAME               0 (x)
              4 LOAD_CONST               1 (None)
              6 RETURN_VALUE
```

注意这里Number of locals是0

## 行号表

参考CPython [Objects/lnotab_notes.txt](https://github.com/python/cpython/blob/3.6/Objects/lnotab_notes.txt)

## Stack size

Code object的Stack size必须大于等于执行过程中可能的最大Stack size，不然可能会引发解释器崩溃

## 生成 pyc 文件

[importlib._bootstrap_external._code_to_bytecode](https://github.com/python/cpython/blob/3.6/Lib/importlib/_bootstrap_external.py#L497)

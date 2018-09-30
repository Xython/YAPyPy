
# Internal Python

一切关于Python的AST(抽象语法树), Bytecode(字节码), 以及语义行为的指南。

## Python指令集

Python如何运行? Python在栈帧上解释code objects(`types.CodeType`)。

在2018年，对于code objects, 我们需要关心的问题是:

### 字节码

这是code object的一个属性, 类型为bytes, 可以通过`codeobj.co_code`拿到.

```python
import dis

def f(a, b):
   return a + b
dis.dis(f.__code__)
>

  2           0 LOAD_FAST                0 (a)
              2 LOAD_FAST                1 (b)
              4 BINARY_ADD
              6 RETURN_VALUE
```

上面的代码这样解释:

> `f.__code__` 是函数f的code object, 描述了函数是如何执行的。
> `LOAD_FAST` 的意思是从局部作用域取出变量, `0 (a)`是dis.dis函数进行inspection的结果，
> 它表示源码中名为a的变量存储在局部变量的第0个位置。
> 当a和b被加载到栈帧上后, `BINARY_ADD`指令消耗栈帧尾部的两个数据，将二者相加，并将结果添加到栈帧尾部。

所有指令及其行为描述在 https://docs.python.org/3/library/dis.html#python-bytecode-instructions 可以全部找到.

### 符号所处的作用域

分为3种，`局部变量`(bound/local), `自由变量`(free)和`全局变量`(global).

自由变量相对于当前作用域而言，来自外部。

```python
def f(x):
    def g(y):
        return x + y # x对于函数g内部的作用域而言是外部的，x是自由的
    return g
```


加载/存储 这些符号对应的数据时，指令是不同的:

| 作用域 | 加载指令      | 存储指令       |
|--------|---------------|----------------|
| 局部   | `LOAD_FAST`   | `STORE_FAST`   |
| 自由   | `LOAD_DEDEF`  | `STORE_DEREF`  |
| 全局   | `LOAD_GLOBAL` | `STORE_GLOBAL` |

还有一个特殊的点要注意, 如果需要加载或者存取自由变量, 那么它必须在外部作用域创建当前的函数对象时，被加载为`closure`(闭包), 指令为`LOAD_CLOSURE`.

```python

def f(x):
    def g(y):
        return x + y
    return g

dis.dis(f.__code__)  # f的字节码
  2           0 LOAD_CLOSURE             0 (x)  # 注意到这里将x加载为闭包
              2 BUILD_TUPLE              1
              4 LOAD_CONST               1 (code g)
              6 LOAD_CONST               2 ('f.<locals>.g')
              8 MAKE_FUNCTION            8
             10 STORE_FAST               1 (g)

  4          12 LOAD_FAST                1 (g)
             14 RETURN_VALUE

dis.dis(f.__code__.co_consts[1])  # 这是g的字节码

  3           0 LOAD_DEREF               0 (x)
              2 LOAD_FAST                0 (y)
              4 BINARY_ADD
              6 RETURN_VALUE
```

全局变量存取是通过哈希表进行的，而自由变量(当然局部也是)是通过一个定长且不可变的序列结构(你可以理解为Python的tuple)进行存取的。

### Code flags

- NoFree

顾名思义, 就是没有自由变量.

```
@dis.show_code
def f(x):
   return 1 + x

>
Name:              f
Filename:          <ipython-input-3-c8a9027a7ab2>
Argument count:    1
Kw-only arguments: 0
Number of locals:  1
Stack size:        2
Flags:             OPTIMIZED, NEWLOCALS, NOFREE  #   没有自由变量
Constants:
   0: None
   1: 1
Variable names:
   0: x
```

而存在自由变量时:

```
call_arg = lambda arg: lambda f: f(arg)

@call_arg(1)
def f(x):
   @dis.show_code
   def g(y):
      return x + y

>
Name:              g
Filename:          <ipython-input-19-725076c6f0b6>
Argument count:    1
Kw-only arguments: 0
Number of locals:  1
Stack size:        2
Flags:             OPTIMIZED, NEWLOCALS, NESTED  # 现在没有NoFree了
Constants:
   0: None
Variable names:
   0: y
Free variables:
   0: x

```

注意，Python中全局变量不作为自由变量处理。

```python

y = 1
@dis.show_code
def f(x):
   return x + y

>
Name:              f
Filename:          <ipython-input-20-97db51fab58c>
Argument count:    1
Kw-only arguments: 0
Number of locals:  1
Stack size:        2
Flags:             OPTIMIZED, NEWLOCALS, NOFREE  # 没有自由变量
Constants:
   0: None
Names:
   0: y
Variable names:
   0: x

```

因为模块顶层的东西都是全局变量:

```python
y = 1
@dis.dis
def f(x):
   return x + y
  4           0 LOAD_FAST                0 (x)
              2 LOAD_GLOBAL              0 (y)  # 注意到y被LOAD_GLOBAL加载
              4 BINARY_ADD
              6 RETURN_VALUE

```

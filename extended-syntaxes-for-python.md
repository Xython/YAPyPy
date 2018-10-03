
# Python语法扩展

源码见: [yapypy/extended_python](./yapypy/extended_python)

## 背景

长期以来, 对于Python语法扩展的呼声都很高。

- 模式匹配:

    https://mail.python.org/pipermail/python-ideas/2015-April/032907.html

    https://mail.python.org/pipermail/python-ideas/2017-June/045963.html

    https://mail.python.org/pipermail/python-ideas/2018-September/053526.html

    也有无数的实现:

    http://www.grantjenks.com/docs/pypatt-python-pattern-matching/#alternatives


- 宏

   https://github.com/lihaoyi/macropy

   https://mail.python.org/pipermail/python-ideas/2013-May/020499.html

   https://bitbucket.org/birkenfeld/karnickel


- 表达式与语句统一

   这个主题并没有太多相关的资料, 但语句和表达式的分离的确阻止了一些有益的程序组合。

   https://mail.python.org/pipermail/python-ideas/2013-August/022971.html

   https://www.python.org/dev/peps/pep-0572/

   任何组合语句的结果不能被表达式使用，除非它处于函数内部。鉴于Python函数调用
   代价昂贵, 在部分场景不可用。


鉴于我们现在用Python实现了Python, 那么实现一个完全兼容原生Python的扩展版本实在是轻而易举的事情。

但是, 注意, 我们现在只是实现了Python的parser, 所以我们只能**加糖**, 但是做不出现有语法写不出的东西,
例如在表示式内以非魔法的方式进行赋值。

而当我们实现bytecode的emitter之后, 我们能做任何事情。

附: PEP572相关文法 https://github.com/Rosuav/cpython/blob/assignment-expressions/Grammar/Grammar

## 设计(初稿)

### 块表达式的workaround

正常的块表达式在Python现有的tokenizer和缩进语法下是无法实现的, 原因是**表达式内部不计缩进级别**

```
(with f:
    return f(1)) + 2
```

上述代码被tokenize之后, 并没得到任何`INDENT` tokenizer。

```
TokenInfo(type=59 (BACKQUOTE), string='utf-8', start=(0, 0), end=(0, 0), line='')
TokenInfo(type=58 (NL), string='\n', start=(1, 0), end=(1, 1), line='\n')
TokenInfo(type=53 (OP), string='(', start=(2, 0), end=(2, 1), line='(with f:\n')
TokenInfo(type=1 (NAME), string='with', start=(2, 1), end=(2, 5), line='(with f:\n')
TokenInfo(type=1 (NAME), string='f', start=(2, 6), end=(2, 7), line='(with f:\n')
TokenInfo(type=53 (OP), string=':', start=(2, 7), end=(2, 8), line='(with f:\n')
TokenInfo(type=58 (NL), string='\n', start=(2, 8), end=(2, 9), line='(with f:\n')
TokenInfo(type=1 (NAME), string='return', start=(3, 4), end=(3, 10), line='    return f(1)) + 2\n')
TokenInfo(type=1 (NAME), string='f', start=(3, 11), end=(3, 12), line='    return f(1)) + 2\n')
TokenInfo(type=53 (OP), string='(', start=(3, 12), end=(3, 13), line='    return f(1)) + 2\n')
TokenInfo(type=2 (NUMBER), string='1', start=(3, 13), end=(3, 14), line='    return f(1)) + 2\n')
TokenInfo(type=53 (OP), string=')', start=(3, 14), end=(3, 15), line='    return f(1)) + 2\n')
TokenInfo(type=53 (OP), string=')', start=(3, 15), end=(3, 16), line='    return f(1)) + 2\n')
TokenInfo(type=53 (OP), string='+', start=(3, 17), end=(3, 18), line='    return f(1)) + 2\n')
TokenInfo(type=2 (NUMBER), string='2', start=(3, 19), end=(3, 20), line='    return f(1)) + 2\n')
TokenInfo(type=4 (NEWLINE), string='\n', start=(3, 20), end=(3, 21), line='    return f(1)) + 2\n')
TokenInfo(type=0 (ENDMARKER), string='', start=(4, 0), end=(4, 0), line='')
```

而要parse一个`with`语句, 当块语句换行时, 必然需要一个`INDENT` tokenizer。
这直接阻止了任何在表达式内部嵌入语句的语法尝试。

我们当然可以重写lexer, 换一套兼容现有缩进规则的parser实现, 例如ML语言的缩进。

但是, 远离标准库是一种不被信任的行为。 一旦你在未经商讨的情形下对Python实现做出大的改动, 你的东西就将被人们忽视、避讳。

对此我给出的解决方案是使用后缀定义 + call by need
```
f(y) with:
    x: count1 + count2
    y:
      if x < 0:
         with storage:
            x = storage.count + x
      x
```
`with`后缀可用于任何语句的末尾, 它惰性地定义了一些变量, 只要当这些变量真正被语句使用时, 他们才会被
当场求值。

在有真正块表达式的语言中, 上述代码等效于
```
f({
    y = a + b
    if y > 0 {
        use storage {
            y = storage.count + y
        }
    }
    y
})
```

### 模式匹配

```python
# match语句
from dataclasses import dataclass
@dataclass
class S:
    x: int
    y: int

match S(1, 2):
    S(a, b):
        print(a, b)
    else:
        pass


# match表达式

match S(1, 2) as S(a, b) return a + b

match S(1, 2) as S(a, b) return a + b\
              as S(2, 3) return 0
```

由于Python的import机制, 很多静态分析的操作无法被应用。例如, 对于某个import的对象,
你无法知道它是否真的是类型的构造器:
```
from my_data import S

match S(1, 2) as S(a, b) # Python的编译期我们无法拿到有关S的任何信息, 也就不知道如何做静态匹配。
```

受到一些先驱工作的启发:

- http://coconut-lang.org
- https://github.com/jargonjustin/matchlib
- https://mail.python.org/pipermail/python-ideas/2015-April/032922.html

我们可以使用一种协议方法`__matchN__`来做开销相对很少的动态模式匹配:

```python
class MyData:
    @staticmethod
    def __match__(test):  # enum match
        return True

    @staticmethod
    def __match1__(test):  # 1-ary destruct
        return True, ('a', )

    @staticmethod
    def __match2__(test): # 2-ary destruct
        return True, ('a', 'b')

 match 1:
    MyData      : print(None)
    MyData(a)   : print(a)
    MyData(a, b): print(a, b)
    else        : pass

# 语义上等价于

test = 1
if MyData.__match__(test):
    print(None)
else:
    is_matched, patterns = MyData.__match1__(test)
    if is_matched:
        [a] = patterns
        print(a)
    else:
        is_matched, patterns = MyData.__match2__(test)
        if is_matched:
            [a, b] = patterns
            print(a, b)
        else:
            pass
```

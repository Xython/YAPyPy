
## 实例一 DBG-Lang

见[kizmi/cmd](https://github.com/thautwarm/kizmi/tree/master/kizmi/cmd)和 [kizmi/database](https://github.com/thautwarm/kizmi/tree/master/kizmi/database)

- 用途: 数据库设计维护
- 优势:
    1. 通过极少的DSL代码生成大量目标语言代码, 便于重构、维护。
    2. 为Python ORM组件提供丰富的静态检查, IDE补全友好, 使得编译期可以发现绝大部分错误。
    3. 静态分析schema, 使得DBG脚本生成的Python API能自动管理数据依赖关系。
- 例子: [dbg脚本](https://github.com/thautwarm/kizmi/blob/master/test.dbg), [生成代码](https://github.com/thautwarm/kizmi/blob/master/dbgout.py)

- 使用: 使用setup.py安装后, 使用命令`dbg gen <dbg脚本文件名> <生成python文件名>`

## 实例二 为Python添加扩展语法

见[kizmi/extended_python](https://github.com/thautwarm/kizmi/tree/master/kizmi/extended_python)

该扩展建立在原生Python的编译组件上, 使用了[原生Python的文法](https://github.com/python/cpython/blob/master/Grammar/Grammar),
以及原生CPython的lexer, 以及CPython虚拟机。

- 目标:
    1. 以纯Python实现Python的parser以及Python字节码编译器(非必要)。

    2. 添加block, match, macro的语法, 设计语义, 实现AST。

    3. 原生AST和扩展AST结构编译到Python字节码。

        Python本身提供了编译api, `compile`函数, 但只能将标准的AST编译到字节码。
        为了将我们的三种扩展AST编译到字节码上，我们有两种选择。

        第一种是, 将扩展的AST转换为标准的AST。因为Python是完备的语言, 所以类似语法糖的三种语法自然可以
        直接转换成原生语法得以实现。

        第二种是, 为扩展的AST实现字节码编译方法。如果只是对三种扩展AST实现编译方法，自然是容易的。但由于
        Python3移除了可供用户扩展的编译模块, 只留下无法扩展的`compile`函数, 所以, 如果只是用纯Python,
        还需要我们也为所有原生的Python AST实现字节码编译方法。


- 关于实现:

    利用[RBNF](https://github.com/thautwarm/RBNF)实现Python的Python parser, [grammar.py](https://github.com/thautwarm/kizmi/tree/master/kizmi/extended_python/grammar.py).

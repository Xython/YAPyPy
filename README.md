
## 实例一 DBG-Lang

- 用途: 数据库设计维护
- 优势:
    1. 通过极少的DSL代码生成大量目标语言代码, 便于重构、维护。
    2. 为Python ORM组件提供丰富的静态检查, IDE补全友好, 使得编译期可以发现绝大部分错误。
    3. 静态分析schema, 使得DBG脚本生成的Python API能自动管理数据依赖关系。
- 例子: [dbg脚本](https://github.com/thautwarm/kizmi/blob/master/test.dbg), [生成代码](https://github.com/thautwarm/kizmi/blob/master/dbgout.py)

- 使用: 使用setup.py安装后, 使用命令`dbg gen <dbg脚本文件名> <生成python文件名>`

## 实例二 为Python添加扩展语法

该扩展建立在原生Python的编译组件上, 使用了[原生Python的文法](https://github.com/python/cpython/blob/master/Grammar/Grammar),
以及原生CPython的lexer, 以及CPython虚拟机。

- 目标:
    1. 为Python添加block语法, 统一表达式和语句(例如多行lambda)
    2. 为Python添加match语法, 提供模式匹配组件
    3. 为Python添加macro语法, 提供便利的ast重写机制
    4. (待定)使用纯python实现一套python字节码编译器。

        前面三个目标的实现，会分别为三个语法实现扩展ast,
        但这三个扩展ast只是被转换到python internal ast上, 而无法直接编译到字节码。这会导致一些性能上的问题。

        Python2 曾经有一个compiler模块提供了可供用户扩展的emit API, 但不幸的是, 后来它被ast模块合并,
        并被移除了最有意义的功能。




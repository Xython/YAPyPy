
## 实例一 DBG-Lang

- 用途: 数据库设计维护
- 优势:
    1. 通过极少的DSL代码生成大量目标语言代码, 便于重构、维护。
    2. 为Python ORM组件提供丰富的静态检查, IDE补全友好, 使得编译期可以发现绝大部分错误。
    3. 静态分析Schema, 使得DBG脚本生成的Python API能自动管理数据依赖关系。
- 例子: [dbg脚本](https://github.com/thautwarm/kizmi/blob/master/test.dbg), [生成代码](https://github.com/thautwarm/kizmi/blob/master/dbgout.py)

- 使用: 使用setup.py安装后, 使用命令`dbg gen <dbg脚本文件名> <生成python文件名>`
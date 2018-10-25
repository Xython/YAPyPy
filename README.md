# YAPyPy ![](https://travis-ci.org/Xython/YAPyPy.svg?branch=master)  [![Coverage Status](https://coveralls.io/repos/github/Xython/YAPyPy/badge.svg?branch=master)](https://coveralls.io/github/Xython/YAPyPy?branch=master)

Yet Another Python Python(YAPyPy), which is extended from and compatible to the original CPython.

Why YAPyPy?

- Compatibility:

    With YAPyPy in Python3.6+, you can run any Python 3.x source codes with full compatibilities.


- Scalability:

    Pattern matching and other popular syntax sugars would be added.

    Anything could be implemented in a trivial way through **multiphase Python**(
    interpreters are provided for you to change ASTs or even calculate constant values/procedure structures before bytecode emitted).


- Optimization:

    You can write your own passes to optimize Python bytecode in specific scenes, or even perform
    JIT techniques when it's possible.
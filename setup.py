from setuptools import setup
from Redy.Tools.Version import Version
from Redy.Tools.PathLib import Path
#
# with open('./README.md', encoding='utf-8') as f:
#     readme = f.read()
readme = ""

setup(
    name='kizmi',
    version='0.1',
    keywords='examples to show how to perform meta-programming in Python',
    description='PyCon 2018 archives for thautwarm',
    long_description=readme,
    long_description_content_type='text/markdown',
    license='MIT',
    python_requires='>=3.6.0',
    url='https://github.com/thautwarm/kizmi',
    author='thautwarm',
    author_email='twshere@outlook.com',
    packages=['kizmi', 'kizmi.cmd', 'kizmi.database', 'kizmi.extended_python'],
    entry_points={
        'console_scripts': [
            'dbg=kizmi.cmd.cli:dbg_lang_cli',
            'python-ex=kizmi.cmd.cli:python_ex_cli'
        ]
    },
    install_requires=[
        'Redy', 'rbnf>=0.3.21', 'wisepy', 'bytecode==0.7.0', 'toolz'
    ],
    platforms='any',
    classifiers=[
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: Implementation :: CPython'
    ],
    zip_safe=False)

from setuptools import setup
import yapypy

#
# with open('./README.md', encoding='utf-8') as f:
#     readme = f.read()
readme = ""

setup(
    name='yapypy',
    version=yapypy.__version__,
    keywords='python implementation, compiler, syntax extension',
    description='Extended and compatible Python written by pure Python',
    long_description=readme,
    long_description_content_type='text/markdown',
    license='MIT',
    python_requires='>=3.6.0',
    url='https://github.com/Xython/YAPyPy',
    author='Xython',
    author_email='twshere@outlook.com',  # billing email
    packages=['yapypy', 'yapypy.cmd', 'yapypy.extended_python', 'yapypy.utils', 'yapypy.extended_python.emit_impl'],
    entry_points={'console_scripts': ['yapypy=yapypy.cmd.cli:python_ex_cli']},
    install_requires=[
        'Redy>=0.2.9', 'rbnf>=0.3.21', 'wisepy', 'bytecode>=0.7.0', 'yapf',
        'astpretty'
    ],
    platforms='any',
    classifiers=[
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: Implementation :: CPython'
    ],
    zip_safe=False
)

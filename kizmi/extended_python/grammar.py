RBNF = \
r"""
NEWLINE := ''
ENDMARKER := ''
NAME := ''
INDENT := ''
DEDENT := ''
NUMBER := ''
STRING := ''

single_input ::= NEWLINE | simple_stmt | compound_stmt NEWLINE
file_input   ::= (NEWLINE | stmt)* ENDMARKER
eval_input   ::= testlist NEWLINE* ENDMARKER

decorator    ::= '@' dotted_name [ '(' [arglist] ')' ] NEWLINE
decorators   ::= decorator+
decorated    ::= decorators (classdef | funcdef | async_funcdef)

async_funcdef ::= 'async' funcdef
funcdef       ::= 'def' NAME parameters ['->' test] ':' suite

parameters    ::= '(' [typedargslist] ')'
typedargslist
            ::=  (tfpdef ['=' test] (',' tfpdef ['=' test])* [',' [
                    '*' [tfpdef] (',' tfpdef ['=' test])* [',' ['**' tfpdef [',']]]
                  | '**' tfpdef [',']]]
                  | '*' [tfpdef] (',' tfpdef ['=' test])* [',' ['**' tfpdef [',']]]
                  | '**' tfpdef [','])
tfpdef ::= NAME [':' test]
varargslist ::= vfpdef ['=' test] (',' vfpdef ['=' test])* [',' [
                '*' [vfpdef] (',' vfpdef ['=' test])* [',' ['**' vfpdef [',']]]
                | '**' vfpdef [',']]]
                | '*' [vfpdef] (',' vfpdef ['=' test])* [',' ['**' vfpdef [',']]]
                | '**' vfpdef [',']

vfpdef ::= NAME

stmt ::= simple_stmt | compound_stmt
simple_stmt ::= small_stmt (';' small_stmt)* [';'] NEWLINE
small_stmt  ::= (expr_stmt | del_stmt | pass_stmt | flow_stmt |
                import_stmt | global_stmt | nonlocal_stmt | assert_stmt)
expr_stmt   ::= testlist_star_expr (annassign | augassign (yield_expr|testlist) |
                     ('=' (yield_expr|testlist_star_expr))*)
annassign   ::= ':' test ['=' test]
testlist_star_expr ::= (test|star_expr) (',' (test|star_expr))* [',']
augassign   ::= ('+=' | '-=' | '*=' | '@=' | '/=' | '%=' | '&=' | '|=' | '^=' |
                '<<=' | '>>=' | '**=' | '//=')
# For normal and annotated assignments, additional restrictions enforced by the interpreter
del_stmt   ::= 'del' exprlist
pass_stmt  ::= 'pass'
flow_stmt  ::= break_stmt | continue_stmt | return_stmt | raise_stmt | yield_stmt
break_stmt ::= 'break'
continue_stmt ::= 'continue'
return_stmt ::= 'return' [testlist_star_expr]
yield_stmt  ::= yield_expr
raise_stmt  ::= 'raise' [test ['from' test]]
import_stmt ::= import_name | import_from
import_name ::= 'import' dotted_as_names
# note below::= the ('.' | '...') is necessary because '...' is tokenized as ELLIPSIS
import_from ::= ('from' (('.' | '...')* dotted_name | ('.' | '...')+)
              'import' ('*' | '(' import_as_names ')' | import_as_names))
import_as_name ::= NAME ['as' NAME]
dotted_as_name ::= dotted_name ['as' NAME]
import_as_names::= import_as_name (',' import_as_name)* [',']
dotted_as_names::= dotted_as_name (',' dotted_as_name)*
dotted_name    ::= NAME ('.' NAME)*
global_stmt    ::= 'global' NAME (',' NAME)*
nonlocal_stmt  ::= 'nonlocal' NAME (',' NAME)*
assert_stmt    ::= 'assert' test [',' test]

compound_stmt  ::= if_stmt | while_stmt | for_stmt | try_stmt | with_stmt | funcdef | classdef | decorated | async_stmt
async_stmt     ::= 'async' (funcdef | with_stmt | for_stmt)
if_stmt        ::= 'if' test ':' suite ('elif' test ':' suite)* ['else' ':' suite]
while_stmt     ::= 'while' test ':' suite ['else' ':' suite]
for_stmt       ::= 'for' exprlist 'in' testlist ':' suite ['else' ':' suite]
try_stmt       ::= ('try' ':' suite
                   ((except_clause ':' suite)+
                    ['else' ':' suite]
                    ['finally' ':' suite] |
                    'finally' ':' suite))

with_stmt      ::= 'with' with_item (',' with_item)*  ':' suite
with_item      ::= test ['as' expr]
except_clause  ::= 'except' [test ['as' NAME]]
suite          ::= simple_stmt | NEWLINE INDENT stmt+ DEDENT

test           ::= or_test ['if' or_test 'else' test] | lambdef
test_nocond    ::= or_test | lambdef_nocond
lambdef        ::= 'lambda' [varargslist] ':' test
lambdef_nocond ::= 'lambda' [varargslist] ':' test_nocond
or_test        ::= and_test ('or' and_test)*
and_test       ::= not_test ('and' not_test)*
not_test       ::= 'not' not_test | comparison
comparison     ::= expr (comp_op expr)*
comp_op        ::= '<'|'>'|'=='|'>='|'<='|'<>'|'!='|'in'|'not' 'in'|'is'|'is' 'not'
star_expr      ::= '*' expr
expr           ::= xor_expr ('|' xor_expr)*
xor_expr       ::= and_expr ('^' and_expr)*
and_expr       ::= shift_expr ('&' shift_expr)*
shift_expr     ::= arith_expr (('<<'|'>>') arith_expr)*
arith_expr     ::= term (('+'|'-') term)*
term           ::= factor (('*'|'@'|'/'|'%'|'//') factor)*
factor         ::= ('+'|'-'|'~') factor | power
power          ::= atom_expr ['**' factor]
atom_expr      ::= [a='await'] atom=atom trailers=trailer*
                   -> atom_expr_rewrite(a, atom, trailers)

atom           ::= (gen ='(' comp=[yield_expr|testlist_comp] ')' |
                    list='[' comp=[testlist_comp]            ']' |
                       '{' dict=[dictorsetmaker] '}' |
                       name=NAME |
                       number=NUMBER | 
                       strs=STRING+ | 
                       ellipsis='...' | 
                       namedc='None' | 
                       namedc='True' | 
                       namedc='False')
                       ->
                           Name(**(loc @ name), id=name.value, ctx=Load()) if name else\
                           Number(**(loc @ number), v=number.value) if number else\
                           str_maker(*strs) if strs else\
                           Ellipsis() if ellipsis else\
                           NamedConstant(**(loc@namedc), vlaue=namedc.value) if namedc else\
                           dict if dict else\
                           comp(is_tuple=True) if gen else\
                           comp(is_list=True) if lisp else\
                           raise_exp(TypeError) 
                                          
testlist_comp  ::= values<<(test|star_expr) ( comp=comp_for | (',' values<<(test|star_expr))* [','] )
                   ->
                     def app(is_tuple=None, is_list=None):
                        if is_list and comp:
                            return ListComp(*values, comp)
                        elif is_list:
                            return List(values, Load())
                        elif comp:
                            return GeneratorExp(*values, comp)
                        else:
                            return Tuple(values, Load())
                     app

# `ExtSlice` is ignored here. We don't need this optimization for this project.
trailer        ::= mark='(' [arglist=arglist] ')' | mark='[' subscr=subscriptlist ']' | mark='.' attr=NAME
                    -> args, kwargs = split_args_helper(arglist)
                       (lambda value: Slice(**(loc @ mark), value=value, slice=subscr )) if subscr else\
                       (lambda value: Call( **(loc @ mark), func =value,  args=args, keywords=kwargs)) if arglist else\
                       (lambda value: Attribute( **(loc @ mark), value=value,  attr=attr.value))
                       
subscriptlist  ::= head=subscript (',' tail << subscript)* [',']
                   ->  Index(head) if not tail else Tuple([head, *tail], Load())                                      
subscript3     ::= [lower=test] ':' [upper=test] [':' [step=test]] -> Slice(lower, upper, step)                        
subscript      ::= it=(test | subscript3) -> it
exprlist       ::= seq << (expr|star_expr) (',' seq << (expr|star_expr))* [','] -> seq
testlist       ::= seq << test (',' seq << test)* [','] -> seq

dict_unpack_s  ::= '**' -> None                
dictorsetmaker ::= (((keys<<test ':' values<<test | keys<<dict_unpack_s values<<expr)
                     (comp=comp_for | (',' (keys<<test ':' values<<test | keys<<dict_unpack_s values<<expr))* [','])) |
                    (values<<(test | star_expr)
                     (comp=comp_for | (',' values<<(test | star_expr))* [','])) )
                    -> if not comp: return Dict(keys, values) if keys else Set(values)
                       DictComp(*keys, *values, comp) if keys else SetComp(*values, comp)

classdef ::= mark='class' name=NAME ['(' [arglist=arglist] ')'] ':' suite
             -> args, kwargs = split_args_helper(arglist)
                ClassDef(**(loc @ mark), name=name.value, bases=args, keywords=kwargs, body=suite, decorator_list=[])

arglist   ::= argument (',' argument)*  [',']

argument  ::= ( test [comp_for] |
                test '=' test |
                '**' test |
                '*' test )

comp_for_item ::= [is_async='async'] 'for' target=exprlist 'in' iter=or_test ('if' ifs<<test_nocond)* 
                  -> comprehension(target, iter, ifs, bool(is_async))
comp_for      ::= generators=comp_for_item+ -> list(generators)

encoding_decl ::= NAME

yield_expr    ::= 'yield' ['from' test | testlist_star_expr]
"""

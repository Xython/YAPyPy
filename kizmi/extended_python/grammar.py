RBNF = r"""
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


parameters    ::= '(' [args=typedargslist] ')' -> args if args else arguments([], None, [], [], None, [])
lam_args      ::= [args=varargslist]           -> args if args else arguments([], None, [], [], None, [])

default_fp    ::= ['=' expr=test] -> expr 

typedargslist ::=  (args << tfpdef defaults<<default_fp (',' args<<tfpdef defaults<<default_fp)* [',' [
                    '*' [vararg=tfpdef] (',' kwonlyargs<<tfpdef kw_defaults<<default_fp)* [',' ['**' kwarg=tfpdef [',']]]
                   | '**' kwarg=tfpdef [',']]]
                   | '*' [vararg=tfpdef] (',' kwonlyargs<<tfpdef kw_defaults<<default_fp)* [',' ['**' kwarg=tfpdef [',']]]
                   | '**' kwarg=tfpdef [','])  
                   -> arguments(args or [], vararg, kwonlyargs or [], kw_defaults or [], kwarg, defaults or [])
                   
tfpdef ::= name=NAME [':' annotation=test] -> arg(name.value, annotation, **loc @ name) 

varargslist ::= args << vfpdef defaults<<default_fp (',' args<<vfpdef defaults<<default_fp)* [',' [
                 '*' [vararg=vfpdef] (',' kwonlyargs<<vfpdef kw_defaults<<default_fp)* [',' ['**' kwarg=vfpdef [',']]]
                | '**' kwarg=vfpdef [',']]]
                | '*' [vararg=vfpdef] (','kwonlyargs<<vfpdef kw_defaults<<default_fp)* [',' ['**' kwargs=vfpdef [',']]]
                | '**' kwargs=vfpdef [',']
                -> arguments(args or [], vararg, kwonlyargs or [], kw_defaults or [], kwarg, defaults or [])

vfpdef ::= name=NAME                      -> arg(name.value, None, **loc @ name)

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

test           ::= it=(ifexp| lambdef)                                  -> it

ifexp          ::= body=or_test ['if' test=or_test 'else' orelse=test]  -> IfExp(test, body, orelse) if orelse else body 
test_nocond    ::= it=(or_test | lambdef_nocond)                        -> it         

lambdef        ::= m='lambda' args=lam_args ':' body=test               -> Lambda(lam_args, body) 
lambdef_nocond ::= m='lambda' args=lam_args ':' body=test_nocond        -> Lambda(lam_args, body)

or_test        ::= seq<<and_test ('or' seq<<and_test)*                  -> BoolOp(Or(), seq)
and_test       ::= seq<<not_test ('and' seq<<not_test)*                 -> BoolOp(And(), seq)
not_test       ::= mark='not' expr=not_test | comp=comparison           -> UnaryOp(Not(), expr, **loc @ mark) if mark else comp 

comparison     ::= left=expr (ops<<comp_op comparators<<expr)*          -> Compare(left, ops, comparators) if ops else left

comp_op        ::= op=('<'|'>'|'=='|'>='|'<='|'<>'|'!='
                        |'in'|'not' 'in'|'is'|'is' 'not')               -> comp_op_rewrite(op)

star_expr      ::= mark='*' expr=expr                                   -> Starred(expr, Load(), **loc @ mark)
expr_tr        ::= op='|' expr=xor_expr                                 -> (op, expr)
expr           ::= head=xor_expr tail=expr_tr*                          -> expr_rewrite(head, tail)

xor_expr_tr    ::= op='^' expr=and_expr                                 -> (op, expr) 
xor_expr       ::= head=and_expr tail=xor_expr_tr*                      -> xor_expr_rewrite(head, tail)

and_expr       ::= seq<<shift_expr ('&' seq<<shift_expr)*               -> and_expr_rewrite(seq)

shift_expr_tr  ::= op=('<<'|'>>') expr=arith_expr                       -> (op, expr)
shift_expr     ::= head=arith_expr tail=shift_expr_tr*                  -> shift_expr_rewrite(head, tail)

arith_expr_tr  ::= op=('+'|'-') expr=term                               -> (op, expr)
arith_expr     ::= head=term tail=arith_expr_tr*                        -> arith_expr_rewrite(head, tail)                        

term_tr        ::= op=('*'|'@'|'/'|'%'|'//') expr=factor                -> (op, expr)
term           ::= head=factor tail=term_tr*                            -> term_rewrite(head, tail)

factor         ::= mark=('+'|'-'|'~') factor=factor | power=power       -> factor_rewrite(mark, factor, power)          

power          ::= atom_expr=atom_expr ['**' factor=factor]             -> BinOp(atom_expr, Pow(), factor) if factor else  atom_expr
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
                    -> args, kwargs = split_args_helper(arglist or [])
                       (lambda value: Slice(**(loc @ mark), value=value, slice=subscr )) if subscr else\
                       (lambda value: Call( **(loc @ mark), func =value,  args=args, keywords=kwargs)) if arglist else\
                       (lambda value: Attribute( **(loc @ mark), value=value,  attr=attr.value))
                       
# `Index` will be deprecated in Python3.8. 
# See https://github.com/python/cpython/pull/9605#issuecomment-425381990                        
subscriptlist  ::= head=subscript (',' tail << subscript)* [',']
                   ->  Index(head if not tail else Tuple([head, *tail], Load()))                                      
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

classdef ::= mark='class' name=NAME ['(' [arglist=arglist] ')'] ':' suite=suite
             -> args, kwargs = split_args_helper(arglist or [])
                ClassDef(name.value, args, kwargs, suite, [], **loc @ mark)

arglist   ::= seq<<argument (',' seq<<argument)*  [','] -> seq

argument  ::= ( arg=test [comp=comp_for] |
                key=test '=' value=test |
                mark='**' kwargs=test |
                mark='*'  args=test )
                -> 
                  Starred(**(loc @ mark), value=args, ctx=Load()) if args else  \
                  keyword(**(loc @ mark), arg=None, value=kwargs) if kwargs else\
                  keyword(**(loc @ key), arg=key, value=value)    if key else   \
                  GeneratorExp(arg, comp)                         if comp else  \
                  arg

comp_for_item ::= [is_async='async'] 'for' target=exprlist 'in' iter=or_test ('if' ifs<<test_nocond)* 
                  -> comprehension(target, iter, ifs, bool(is_async))
                  
comp_for      ::= generators=comp_for_item+ -> list(generators)

encoding_decl ::= NAME

yield_expr    ::= mark='yield' [is_yield_from='from' expr=test | expr=testlist_star_expr]
                  -> YieldFrom(**(loc @ mark), value=expr) if is_yield_from else Yield(**(loc @ mark), value=expr)
"""

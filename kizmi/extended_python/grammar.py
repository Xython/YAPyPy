RBNF = r"""
NEWLINE := ''
ENDMARKER := ''
NAME := ''
INDENT := ''
DEDENT := ''
NUMBER := ''
STRING := ''

single_input ::= it=NEWLINE | seq=simple_stmt | it=compound_stmt NEWLINE
file_input   ::= (NEWLINE | seqs<<stmt)* ENDMARKER -> mod=Module(sum(seqs, [])); fix_missing_locations(mod); return mod
eval_input   ::= it=testlist NEWLINE* ENDMARKER -> Expression(it)

# the restrictions of decorator syntax are released here for the sake of convenience.
decorator    ::= '@' exp=test NEWLINE                                                   -> exp
decorated    ::= decorators=decorator+ it=(classdef | funcdef | async_funcdef)          -> it.decorator_list = list(decorators); return it
                
async_funcdef ::= mark='async' name=NAME args=parameters ['->' ret=test] ':' body=suite -> def_rewrite(mark, name, args, ret, body, is_async=True) 
funcdef       ::= mark='def' name=NAME args=parameters ['->' ret=test] ':' body=suite   -> def_rewrite(mark, name, args, ret, body)


parameters    ::= '(' [args=typedargslist] ')'                                          -> args if args else arguments([], None, [], [], None, [])
lam_args      ::= [args=varargslist]                                                    -> args if args else arguments([], None, [], [], None, [])

default_fp    ::= '=' expr=test                                                         -> expr
kw_default_fp ::= ['=' expr=test]                                                       -> expr 
tfpdef ::= name=NAME [':' annotation=test]                                              -> arg(name.value, annotation, **loc @ name) 
vfpdef ::= name=NAME                                                                    -> arg(name.value, None, **loc @ name)

typedargslist ::=  args << tfpdef [defaults<<default_fp] (',' args<<tfpdef [defaults<<default_fp])* [',' [
                    '*' [vararg=tfpdef] (',' kwonlyargs<<tfpdef kw_defaults<<kw_default_fp)* [',' ['**' kwarg=tfpdef [',']]]
                   | '**' kwarg=tfpdef [',']]]
                   | '*' [vararg=tfpdef] (',' kwonlyargs<<tfpdef kw_defaults<<kw_default_fp)* [',' ['**' kwarg=tfpdef [',']]]
                   | '**' kwarg=tfpdef [',']                                           
                   -> arguments(args or [], vararg, kwonlyargs or [], kw_defaults or [], kwarg, defaults or [])


varargslist ::= args << vfpdef [defaults<<default_fp] (',' args<<vfpdef [defaults<<default_fp])* [',' [
                 '*' [vararg=vfpdef] (',' kwonlyargs<<vfpdef kw_defaults<<kw_default_fp)* [',' ['**' kwarg=vfpdef [',']]]
                | '**' kwarg=vfpdef [',']]]
                | '*' [vararg=vfpdef] (','kwonlyargs<<vfpdef kw_defaults<<kw_default_fp)* [',' ['**' kwargs=vfpdef [',']]]
                | '**' kwargs=vfpdef [',']    
                -> arguments(args or [], vararg, kwonlyargs or [], kw_defaults or [], kwarg, defaults or [])

stmt        ::= seq=simple_stmt | it=compound_stmt                                                            -> [it] if it else seq
simple_stmt ::= seq<<small_stmt (';' seq<<small_stmt)* [';'] NEWLINE                                          -> seq
small_stmt  ::= it=(expr_stmt | del_stmt | pass_stmt | flow_stmt |                                            # ------------------------------
                import_stmt | global_stmt | nonlocal_stmt | assert_stmt)                                      -> it
expr_stmt   ::= lhs=testlist_star_expr (ann=annassign | aug=augassign aug_exp=(yield_expr|testlist) |         # ------------------------------
                     ('=' rhs<<(yield_expr|testlist_star_expr))*)                                             -> expr_stmt_rewrite(lhs, ann, aug, aug_exp, rhs)
annassign   ::= ':' anno=test ['=' value=test]                                                                -> (anno, value)
testlist_star_expr ::= seq<<(test|star_expr) (',' seq<<(test|star_expr))* [force_tuple=',']                   -> Tuple(seq) if len(seq) > 1 or force_tuple else seq[0]                                                
augassign   ::= it=('+=' | '-=' | '*=' | '@=' | '/=' | '%=' | '&=' | '|=' | '^=' |                            # ------------------------------
                    '<<=' | '>>=' | '**=' | '//=')                                                            -> augassign_rewrite(it)
# For normal and annotated assignments, additional restrictions enforced by the interpreter                   -------------------------------
del_stmt   ::= mark='del' tp=exprlist                                                                         -> Delete(tp.elts if isinstance(tp, Tuple) else [tp], **loc @ mark)
pass_stmt  ::= mark='pass'                                                                                    -> Pass(**loc @ mark)
flow_stmt  ::= it=(break_stmt | continue_stmt | return_stmt | raise_stmt | yield_stmt)                        -> it
break_stmt ::= mark='break'                                                                                   -> Break(**loc @ mark)
continue_stmt ::= mark='continue'                                                                             -> Continue(**loc @ mark)
return_stmt ::= mark='return' [value=testlist_star_expr]                                                      -> Return(value, **loc @ mark)
yield_stmt  ::= exp=yield_expr                                                                                -> Expr(exp)                                    
raise_stmt  ::= mark='raise' [exc=test ['from' cause=test]]                                                   -> Raise(exc, cause, **loc @ mark) 
import_stmt ::= it=(import_name | import_from)                                                                -> it 
import_name ::= mark='import' names=dotted_as_names                                                            -> Import(names, **loc @ mark)
# note below::= the ('.' | '...') is necessary because '...' is tokenized as ELLIPSIS                         --------------------------------
import_level::= (_1='.' | '...')                                                                              -> 1 if _1 else 3                                                           
wild        ::= '*'                                                                                           -> [alias(name='*', asname=None)]
import_from ::= (mark='from' (levels=('.' | '...')* module=dotted_name | levels=('.' | '...')+)               # ------------------------------
                 'import' (wild=wild | '(' names=import_as_names ')' | names=import_as_names))                 -> ImportFrom(module, wild or names, sum(levels or []), **loc @ mark)                           
NAMESTR        ::= n=NAME                                                                                     -> n.value         
import_as_name ::= name=NAMESTR ['as' asname=NAMESTR]                                                         -> alias(name, asname)
dotted_as_name ::= name=dotted_name ['as' asname=NAMESTR]                                                     -> alias(name, asname) 
import_as_names::= seq<<import_as_name (',' seq<<import_as_name)* [',']                                       -> seq
dotted_as_names::= seq<<dotted_as_name (',' seq<<dotted_as_name)*                                             -> seq
dotted_name    ::= xs=(NAME ('.' NAME)*)                                                                      -> ''.join(c.value for c in xs)
global_stmt    ::= mark='global' names<<NAMESTR (',' name<<NAMESTR)*                                          -> Global(names, **loc @ mark)                                                         
nonlocal_stmt  ::= mark='nonlocal' names<<NAMESTR (',' name<<NAMESTR)*                                        -> Nonlocal(names, **loc @ mark)
assert_stmt    ::= mark='assert' test=test [',' msg=test]                                                     -> Assert(test, msg, **loc @ mark)
compound_stmt  ::= it=(if_stmt | while_stmt | for_stmt | try_stmt | with_stmt | funcdef | classdef | decorated # ------------------------------
                   | async_stmt)                                                                              -> it
async_stmt     ::= it=(async_funcdef | async_with_stmt | async_for_stmt)                                      -> it
if_stmt        ::=  marks<<'if' tests<<test ':'                                                               # ------------------------------
                        bodies<<suite                                                                         # ------------------------------
                    (marks<<'elif' tests<<test ':' bodies<<suite)*                                            # ------------------------------
                    ['else' ':' orelse=suite]                                                                 -> if_stmt_rewrite(marks, tests, bodies, orelse)
while_stmt     ::= 'while' test=test ':' body=suite ['else' ':' orelse=suite]                                  -> while_stmt_rewrite(test, body, orelse)
async_for_stmt ::= 'async' 'for' target=exprlist 'in' iter=testlist ':' body=suite ['else' ':' orelse=suite]  -> for_stmt_rewrite(target, iter, body, orelse, is_async=True)  
for_stmt       ::= 'for' target=exprlist 'in' iter=testlist ':' body=suite ['else' ':' orelse=suite]          -> for_stmt_rewrite(target, iter, body, orelse)
try_stmt       ::= (mark='try' ':'                                                                            # ---------------------------
                    body=suite                                                                                # ---------------------------
                   ((excs<<except_clause ':' rescues<<suite)+                                                 # ---------------------------
                    ['else' ':' orelse=suite]                                                                 # ---------------------------
                    ['finally' ':' final=suite] |                                                             # ---------------------------
                     'finally' ':' final=suite))                                                              -> try_stmt_rewrite(mark, body, excs, rescues, orelse, final)
async_with_stmt::= mark='async' 'with' items<<with_item (',' items<<with_item)*  ':' body=suite               -> with_stmt_rewrite(mark, items, body, is_async=True)
with_stmt      ::= mark='with' items<<with_item (',' items<<with_item)*  ':' body=suite                       -> with_stmt_rewrite(mark, items, body)
with_item      ::= context_expr=test ['as' optional_vars=expr]                                                -> withitem(context_expr, as_store(optional_vars))                                                       
except_clause  ::= 'except' [type=test ['as' name=NAMESTR]]                                                   -> (type, name)                                                       
suite          ::= seqs<<simple_stmt | NEWLINE INDENT (seqs<<stmt)+ DEDENT                                    -> sum(seqs, [])
test           ::= it=(ifexp| lambdef)                                  -> it
ifexp          ::= body=or_test ['if' test=or_test 'else' orelse=test]  -> IfExp(test, body, orelse) if orelse else body 
test_nocond    ::= it=(or_test | lambdef_nocond)                        -> it         

lambdef        ::= m='lambda' args=lam_args ':' body=test               -> Lambda(lam_args, body) 
lambdef_nocond ::= m='lambda' args=lam_args ':' body=test_nocond        -> Lambda(lam_args, body)

or_test        ::= head=and_test ('or' tail<<and_test)*                  -> BoolOp(Or(), [head, *tail])  if tail else head  
and_test       ::= head=not_test ('and' tail<<not_test)*                 -> BoolOp(And(), [head, *tail]) if tail else head
not_test       ::= mark='not' expr=not_test | comp=comparison           -> UnaryOp(Not(), expr, **loc @ mark) if mark else comp 

comparison     ::= left=expr (ops<<comp_op comparators<<expr)*          -> Compare(left, ops, comparators) if ops else left

comp_op        ::= op=('<'|'>'|'=='|'>='|'<='|'<>'|'!='
                        |'in'|'not' 'in'|'is'|'is' 'not')               -> comp_op_rewrite(op)

star_expr      ::= mark='*' expr=expr                                   -> Starred(expr, Load(), **loc @ mark)
expr_tr        ::= op='|' expr=xor_expr                                 -> (op, expr)
expr           ::= head=xor_expr tail=expr_tr*                          -> expr_rewrite(head, tail)

xor_expr_tr    ::= op='^' expr=and_expr                                 -> (op, expr) 
xor_expr       ::= head=and_expr tail=xor_expr_tr*                      -> xor_expr_rewrite(head, tail)

and_expr       ::= head=shift_expr ('&' tail=shift_expr)*               -> and_expr_rewrite(head, tail)

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
                           Name(name.value, Load(), **loc @ name) if name else\
                           Num(eval(number.value), **loc @ number) if number else\
                           str_maker(*strs) if strs else\
                           Ellipsis() if ellipsis else\
                           NamedConstant(eval(namedc.value), **loc@namedc) if namedc else\
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
trailer        ::= call='(' [arglist=arglist] ')' | mark='[' subscr=subscriptlist ']' | mark='.' attr=NAME
                    -> args, kwargs = split_args_helper(arglist or [])
                       (lambda value: Slice(value, subscr, **loc @ mark)) if subscr else\
                       (lambda value: Call(value, args, kwargs, **loc @ call)) if call else\
                       (lambda value: Attribute(value, attr.value, Load(), **loc @ mark))                       
                       
# `Index` will be deprecated in Python3.8. 
# See https://github.com/python/cpython/pull/9605#issuecomment-425381990                        
subscriptlist  ::= head=subscript (',' tail << subscript)* [',']
                   ->  Index(head if not tail else Tuple([head, *tail], Load()))                                      
subscript3     ::= [lower=test] ':' [upper=test] [':' [step=test]] -> Slice(lower, upper, step)                        
subscript      ::= it=(test | subscript3) -> it
exprlist       ::= seq << (expr|star_expr) (',' seq << (expr|star_expr))* [','] -> seq
testlist       ::= seq << test (',' seq << test)* [force_tuple=','] -> Tuple(seq, Load()) if force_tuple or len(seq) > 1 else seq[0]

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

argument  ::= ( 
                key=NAME '=' value=test |
                arg=test [comp=comp_for] |
                mark='**' kwargs=test |
                mark='*'  args=test )
                -> 
                  Starred(**(loc @ mark), value=args, ctx=Load())    if args else  \
                  keyword(**(loc @ mark), arg=None, value=kwargs)    if kwargs else\
                  keyword(**(loc @ key), arg=key.value, value=value) if key else   \
                  GeneratorExp(arg, comp)                            if comp else  \
                  arg

comp_for_item ::= [is_async='async'] 'for' target=exprlist 'in' iter=or_test ('if' ifs<<test_nocond)* 
                  -> comprehension(target, iter, ifs, bool(is_async))
                  
comp_for      ::= generators=comp_for_item+ -> list(generators)

encoding_decl ::= NAME

yield_expr    ::= mark='yield' [is_yield_from='from' expr=test | expr=testlist_star_expr]
                  -> YieldFrom(**(loc @ mark), value=expr) if is_yield_from else Yield(**(loc @ mark), value=expr)
"""

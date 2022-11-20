import re
import os
from pycparser import CParser, c_ast, c_parser, c_generator
from Exterfun import *
from src.Opt import *
from Witness import *
import signal
import time

HEADER = ""
HEADER_c = "#include \"klee/klee.h\"\n"
TestPath = "/tmp/verioover/"

cur_scope = ""


def set_timeout(num, callback):
    def wrap(func):
        def handle(sig, frame):
            raise RuntimeError


        def to_do(*args, **kwargs):
            try:
                signal.signal(signal.SIGALRM, handle)
                signal.alarm(num)
                r = func(*args, **kwargs)
                signal.alarm(0)
                return r
            except RuntimeError as e:
                callback()

        return to_do
    return wrap

def aftertime():
    print("parser timeout!")

def init(ast):
    haslist = []
    for i in range(len(ast.ext)):
        if isinstance(ast.ext[i] ,c_ast.Decl):
            # if ast.ext[i].storage == ['extern'] and "__VERIFIER_nondet" in ast.ext[i].name:
            if "__VERIFIER_nondet" in ast.ext[i].name:
                funname = ast.ext[i].name
                if funname in haslist:
                    ast.ext[i] = None
                    continue
                haslist.append(funname)
                ast.ext[i] = exterfun[funname][0]
                ast.ext.insert(i, exterfun[funname][1])


def replace_blockitem_verfun(block_items):
    lineno = {}
    scopelist = {}

    if block_items == None:
        return block_items, lineno, scopelist

    for i in range(len(block_items)):
        if isinstance(block_items[i], c_ast.Assignment):
            block_items[i], lno, scl = replace_assexpr_verfun(block_items[i])
            lineno.update(lno)
            scopelist.update(scl)

        elif isinstance(block_items[i], c_ast.Decl):
            block_items[i], lno, scl = replace_decl_verfun(block_items[i])
            lineno.update(lno)
            scopelist.update(scl)

        elif isinstance(block_items[i], c_ast.While):
            block_items[i], lno, scl = replace_while_verfun(block_items[i])
            lineno.update(lno)
            scopelist.update(scl)

        elif isinstance(block_items[i], c_ast.For):
            block_items[i], lno, scl = replace_for_verfun(block_items[i])
            lineno.update(lno)
            scopelist.update(scl)

        elif isinstance(block_items[i], c_ast.If):
            block_items[i], lno, scl = replace_if_verfun(block_items[i])
            lineno.update(lno)
            scopelist.update(scl)

    return block_items, lineno, scopelist



def replace_assexpr_verfun(assexpr):
    lineno = {}
    scopelist = {}

    if isinstance(assexpr.rvalue, c_ast.FuncCall) and "__VERIFIER_nondet" in assexpr.rvalue.name.name:
        if isinstance(assexpr.lvalue, c_ast.UnaryOp):
            g = c_generator.CGenerator()
            lname = g.visit(assexpr.lvalue)
            rname = assexpr.rvalue.name.name
            # change funcation name
            assexpr.rvalue.name.name = rname + "_withname"

            # change funcation args
            args = c_ast.ExprList(exprs=[c_ast.Constant(type="string", value="\"" + lname + "\"")])
            assexpr.rvalue.args = args

            # lineno map
            lineno = {lname: assexpr.lvalue.coord.line}
            scopelist = {lname: cur_scope}

        elif isinstance(assexpr.lvalue, c_ast.ArrayRef):
            g = c_generator.CGenerator()
            lname = g.visit(assexpr.lvalue)
            rname = assexpr.rvalue.name.name
            # change funcation name
            assexpr.rvalue.name.name = rname + "_withname"

            # change funcation args
            args = c_ast.ExprList(exprs=[c_ast.Constant(type="string", value="\"" + lname + "\"")])
            assexpr.rvalue.args = args

            # lineno map
            lineno = {lname: assexpr.lvalue.coord.line}
            scopelist = {lname: cur_scope}

        else:
            lname = assexpr.lvalue.name
            rname = assexpr.rvalue.name.name

            # change funcation name
            assexpr.rvalue.name.name = rname + "_withname"

            # change funcation args
            args = c_ast.ExprList(exprs=[c_ast.Constant(type="string", value="\"" + lname + "\"")])
            assexpr.rvalue.args = args

            # lineno map
            lineno = {lname: assexpr.lvalue.coord.line}
            scopelist = {lname: cur_scope}


        return assexpr, lineno, scopelist
    else:
        return assexpr, lineno, scopelist


def replace_decl_verfun(declexpr):
    lineno = {}
    scopelist = {}


    varname = declexpr.name
    scopelist.update({varname: cur_scope})

    if isinstance(declexpr.init, c_ast.FuncCall):
        funname = declexpr.init.name.name
        varname = declexpr.name

        if "__VERIFIER_nondet" in funname:
            args = c_ast.ExprList(exprs=[c_ast.Constant(type="string", value="\"" + varname + "\"")])
            declexpr.init.args = args
            declexpr.init.name.name += "_withname"
            lineno = {varname: declexpr.coord.line}
            scopelist = {varname: cur_scope}


    return declexpr, lineno, scopelist


def replace_while_verfun(whilestmt):
    lineno = {}
    scopelist = {}

    if isinstance(whilestmt.stmt, c_ast.Compound):
        block_items = whilestmt.stmt.block_items
        whilestmt.stmt.block_items, lno, scl = replace_blockitem_verfun(block_items)
        lineno.update(lno)
        scopelist.update(scl)

    elif isinstance(whilestmt.stmt, c_ast.Assignment):
        whilestmt.stmt, lno, scl = replace_assexpr_verfun(whilestmt.stmt)
        lineno.update(lno)
        scopelist.update(scl)

    elif isinstance(whilestmt.stmt, c_ast.While):
        whilestmt.stmt, lno, scl = replace_while_verfun(whilestmt.stmt)
        lineno.update(lno)
        scopelist.update(scl)

    elif isinstance(whilestmt.stmt, c_ast.For):
        whilestmt.stmt, lno, scl = replace_for_verfun(whilestmt.stmt)
        lineno.update(lno)
        scopelist.update(scl)

    elif isinstance(whilestmt.stmt, c_ast.If):
        whilestmt.stmt, lno, scl = replace_if_verfun(whilestmt.stmt)
        lineno.update(lno)
        scopelist.update(scl)

    return whilestmt, lineno, scopelist


def replace_for_verfun(forstmt):

    stmt = forstmt.stmt
    lineno = {}
    scopelist = {}

    if isinstance(stmt, c_ast.Compound):
        block_items = stmt.block_items
        block_items, lno, scl = replace_blockitem_verfun(block_items)
        lineno.update(lno)
        scopelist.update(scl)

    elif isinstance(stmt, c_ast.For):
        forstmt.stmt, lno, scl = replace_for_verfun(stmt)
        lineno.update(lno)
        scopelist.update(scl)

    elif isinstance(stmt, c_ast.If):
        forstmt.stmt, lno, scl = replace_if_verfun(stmt)
        lineno.update(lno)
        scopelist.update(scl)

    elif isinstance(stmt, c_ast.Assignment):
        forstmt.stmt, lno, scl = replace_assexpr_verfun(stmt)
        lineno.update(lno)
        scopelist.update(scl)

    elif isinstance(stmt, c_ast.While):
        forstmt.stmt, lno, scl = replace_while_verfun(stmt)
        lineno.update(lno)
        scopelist.update(scl)


    return forstmt, lineno, scopelist


def replace_if_verfun(ifexpr):
    lineno = {}
    scopelist = {}

    true_block_items = None
    false_block_items = None

    if isinstance(ifexpr.iftrue, c_ast.Compound):
        true_block_items = ifexpr.iftrue.block_items
        true_block_items, lno, scl = replace_blockitem_verfun(true_block_items)
        lineno.update(lno)
        scopelist.update(scl)
    if isinstance(ifexpr.iffalse, c_ast.Compound):
        false_block_items = ifexpr.iffalse.block_items
        false_block_items, lno, scl = replace_blockitem_verfun(false_block_items)
        lineno.update(lno)
        scopelist.update(scl)

    if isinstance(ifexpr.iftrue, c_ast.Assignment):
        ifexpr.iftrue, lno, scl = replace_assexpr_verfun(ifexpr.iftrue)
        lineno.update(lno)
        scopelist.update(scl)
    if isinstance(ifexpr.iffalse, c_ast.Assignment):
        ifexpr.iffalse, lno, scl = replace_assexpr_verfun(ifexpr.iffalse)
        lineno.update(lno)
        scopelist.update(scl)

    if isinstance(ifexpr.iftrue, c_ast.For):
        ifexpr.iftrue, lno, scl = replace_for_verfun(ifexpr.iftrue)
        lineno.update(lno)
        scopelist.update(scl)
    if isinstance(ifexpr.iffalse, c_ast.For):
        ifexpr.iffalse, lno, scl = replace_for_verfun(ifexpr.iffalse)
        lineno.update(lno)
        scopelist.update(scl)

    if isinstance(ifexpr.iftrue, c_ast.While):
        ifexpr.iftrue, lno, scl = replace_while_verfun(ifexpr.iftrue)
        lineno.update(lno)
        scopelist.update(scl)
    if isinstance(ifexpr.iffalse, c_ast.While):
        ifexpr.iffalse, lno, scl = replace_while_verfun(ifexpr.iffalse)
        lineno.update(lno)
        scopelist.update(scl)

    if isinstance(ifexpr.iftrue, c_ast.If):
        ifexpr.iftrue, lno, scl = replace_if_verfun(ifexpr.iftrue)
        lineno.update(lno)
        scopelist.update(scl)
    if isinstance(ifexpr.iffalse, c_ast.If):
        ifexpr.iffalse, lno, scl = replace_if_verfun(ifexpr.iffalse)
        lineno.update(lno)
        scopelist.update(scl)

    return ifexpr, lineno, scopelist



def replace_sym_fundef(mainfun):
    lineno = {}
    scopelist = {}
    block_items = mainfun.body.block_items

    block_items, lno, scl = replace_blockitem_verfun(block_items)
    lineno.update(lno)
    scopelist.update(scl)

    mainfun.body.block_items = block_items

    return mainfun, lineno, scopelist



def replace_sym(ast):
    lineno = {}
    scopelist = {}
    global cur_scope
    for i in range(len(ast.ext)):
        if isinstance(ast.ext[i], c_ast.FuncDef) and ast.ext[i].decl.name == "main":
            cur_scope = "main"
            ast.ext[i], lno, scl = replace_sym_fundef(ast.ext[i])
            lineno.update(lno)
            scopelist.update(scl)
        elif isinstance(ast.ext[i], c_ast.FuncDef):
            cur_scope = ast.ext[i].decl.name
            ast.ext[i], lno, scl = replace_sym_fundef(ast.ext[i])
            lineno.update(lno)
            scopelist.update(scl)

    return ast, lineno, scopelist

@set_timeout(5, aftertime)
def InsertConcent(filepath, filename):
    linenumber = {}
    varscope = {}
    optflag = False

    if ".i" not in filename:
        f = open(filepath, "r+")
        code = f.read()
        fnew = open(TestPath + filename, "w")

        code = re.sub(r"\/\*(?:[^\*]|\*+[^\/\*])*\*+\/", "", code)
        code = re.sub(r"//.*", "", code)
        code = re.sub(r".*__attribute__.*;", "", code)
        code = re.sub(r".*__extension__.*;", "", code)
        parser = CParser()
        ast = parser.parse(code)
        ast, linenumber, varscope = replace_sym(ast)
        init(ast)

        g = c_generator.CGenerator()

        fnew.write(g.visit(ast))

    else:
        # fnew.write(code)
        raise TypeError
        pass

    fnew.close()

    return linenumber, varscope, ast







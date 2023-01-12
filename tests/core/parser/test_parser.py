#------------------------------------------------------------------------------
# Copyright (c) 2018, Nucleic Development Team.
#
# Distributed under the terms of the Modified BSD License.
#
# The full license is in the file LICENSE, distributed with this software.
#------------------------------------------------------------------------------
import os
import sys
import ast
import enaml
import pytest
import traceback
from textwrap import dedent

from enaml.compat import PY39


def validate_ast(py_node, enaml_node, dump_ast=False, offset=0):
    """Validate each node of an ast against another ast.

    Typically used to compare an AST generated by the Python paser and one
    generated by the enaml parser.

    """
    if dump_ast:
        print('Python node:\n', ast.dump(py_node))
        print('Enaml node:\n', ast.dump(enaml_node))
    assert type(py_node) == type(enaml_node)
    if isinstance(py_node, ast.AST):
        for name, field in ast.iter_fields(py_node):
            if name == 'ctx':
                assert type(field) == type(getattr(enaml_node, name))
            else:
                field2 = getattr(enaml_node, name, None)
                print('    '*offset, 'Validating:', name)
                validate_ast(field, field2, offset=offset+1)
    elif isinstance(py_node, list):
        if len(py_node) != len(enaml_node):
            return False
        for i, n1 in enumerate(py_node):
            print('    '*offset, 'Validating', i+1, 'th element')
            validate_ast(n1, enaml_node[i], offset=offset+1)
    else:
        assert py_node == enaml_node


def test_syntax_error_traceback_correct_path(tmpdir):
    """ Test that a syntax error retains the path to the file

    """
    test_module_path = os.path.join(tmpdir.strpath, 'view.enaml')

    with open(os.path.join(tmpdir.strpath, 'test_main.enaml'), 'w') as f:
        f.write(dedent("""
        from enaml.widgets.api import Window, Container, Label
        from view import CustomView

        enamldef MyWindow(Window): main:
            CustomView:
                pass

        """))

    with open(test_module_path, 'w') as f:
        f.write(dedent("""
        from enaml.widgets.api import Container, Label

        enamldef CustomLabel(Container):
            Label # : missing intentionally
                text = "Hello world"

        """))

    try:
        sys.path.append(tmpdir.strpath)
        with enaml.imports():
            from test_main import MyWindow
        assert False, "Should raise a syntax error"
    except Exception as e:
        tb = traceback.format_exc()
        print(tb)
        lines = tb.strip().split("\n")
        assert ('File "{}", line (5, 35)'.format(test_module_path) in
            (lines[-3] if PY39 else lines[-4]))
    finally:
        sys.path.remove(tmpdir.strpath)

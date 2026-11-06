"""Business-case's one door to the plugin result checker.

The checker is a copy of the standard's file in `schemas/`, loaded here by path. It reads its
sibling schema files from its own folder, so all five files are copied together. Every other
module imports these names and never loads the checker another way.

Python 3.9 syntax only.
"""
from __future__ import annotations

import importlib.util
from pathlib import Path

_CHECKER = Path(__file__).resolve().parent.parent / "schemas" / "plugin_result_check.py"


def _load():
    spec = importlib.util.spec_from_file_location("bc_plugin_result_check", _CHECKER)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


CHECK = _load()


def check_result(doc):
    return CHECK.check_result(doc)


def check_result_file(path):
    return CHECK.check_result_file(path)


def check_answers(doc):
    return CHECK.check_answers(doc)


def check_invocation(block, commands=None):
    return CHECK.check_invocation(block, commands)


def validate(instance, schema):
    return CHECK.validate(instance, schema)


def command_part(command):
    return CHECK.command_part(command)


def load_kinds():
    return CHECK.load_kinds()

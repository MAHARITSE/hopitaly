#!/usr/bin/env python
"""
HealthNet manage.py - Django 1.6.5 compatibility wrapper
Supports modern Python (3.11+) by providing missing modules/classes
that were removed/deprecated after Django 1.6 was released.

Fixes:
  - ModuleNotFoundError: No module named 'imp'  (Python 3.12+)
  - ImportError: cannot import name 'getargspec'
  - AttributeError: 'DjangoTranslation' object has no attribute 'set_output_charset'
  - AttributeError: module 'html.parser' has no attribute 'HTMLParseError'
"""
import os
import sys
import inspect

# =====================================================================
# EARLY COMPATIBILITY PATCHES - MUST RUN BEFORE ANY DJANGO IMPORTS
# =====================================================================

# 1. Patch inspect.getargspec (removed + signature change in Python 3.x)
# Django 1.6 still calls: params, varargs, varkw, defaults = getargspec(func)
# getfullargspec returns 7 values, so we must provide a 4-tuple shim.
def _getargspec_compatible(func):
    """Compatibility replacement for the deprecated inspect.getargspec (4-tuple)."""
    spec = inspect.getfullargspec(func)
    # Return exactly what old getargspec returned: (args, varargs, varkw, defaults)
    return (spec.args, spec.varargs, spec.varkw, spec.defaults)

inspect.getargspec = _getargspec_compatible

# 1b. Patch collections.Iterator (and other ABCs) - moved to collections.abc in Py 3.3+
# Very common issue with Django <= 1.6 on Python 3.3+
import collections
import collections.abc as collections_abc
for name in ("Iterator", "Iterable", "Mapping", "MutableMapping", "Callable", "Sequence"):
    if not hasattr(collections, name) and hasattr(collections_abc, name):
        setattr(collections, name, getattr(collections_abc, name))

# 2. Patch html.parser.HTMLParseError (removed in modern Python)
try:
    import html.parser as _html_parser
    if not hasattr(_html_parser, 'HTMLParseError'):
        class HTMLParseError(Exception):
            """Compatibility shim for Django 1.6"""
            pass
        _html_parser.HTMLParseError = HTMLParseError
except Exception:
    pass

# 3. Patch imp module (completely removed in Python 3.12+)
try:
    import imp
except ImportError:
    try:
        import zombie_imp as imp
        sys.modules['imp'] = imp
    except ImportError:
        # Last resort: minimal stub (some Django features may be limited)
        class _ImpStub:
            @staticmethod
            def find_module(name, path=None):
                return None
            PY_SOURCE = 1
            PY_COMPILED = 2
            C_EXTENSION = 3
            PKG_DIRECTORY = 5
            C_BUILTIN = 6
            PY_FROZEN = 7
        imp = _ImpStub()
        sys.modules['imp'] = imp

# 4. CRITICAL: Patch DjangoTranslation.set_output_charset BEFORE Django loads it.
#    We import the module that defines it and monkey-patch the class.
#    This must happen as early as possible.
try:
    # Force-load the translation module so we can patch it
    import django.utils.translation.trans_real as _trans_real

    _orig_init = _trans_real.DjangoTranslation.__init__

    def _patched_django_translation_init(self, *args, **kwargs):
        # Call the original __init__
        _orig_init(self, *args, **kwargs)
        # Guarantee the method exists (Django 1.6 calls it unconditionally)
        if not hasattr(self, 'set_output_charset'):
            def _set_output_charset(charset):
                self._charset = charset
            self.set_output_charset = _set_output_charset

    _trans_real.DjangoTranslation.__init__ = _patched_django_translation_init

    # Also directly add the method in case __init__ already ran for some reason
    if not hasattr(_trans_real.DjangoTranslation, 'set_output_charset'):
        def _set_output_charset(self, charset):
            self._charset = charset
        _trans_real.DjangoTranslation.set_output_charset = _set_output_charset

except Exception as e:
    # If django is not installed yet, we'll try again inside __main__
    _trans_patch_error = str(e)
else:
    _trans_patch_error = None

# =====================================================================

if __name__ == "__main__":
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "prototype.settings")

    # Re-apply translation patch in case the early one failed
    if _trans_patch_error is not None:
        try:
            import django.utils.translation.trans_real as trans_real
            if not hasattr(trans_real.DjangoTranslation, 'set_output_charset'):
                def _set_output_charset(self, charset):
                    self._charset = charset
                trans_real.DjangoTranslation.set_output_charset = _set_output_charset
        except Exception:
            pass

    from django.core.management import execute_from_command_line

    execute_from_command_line(sys.argv)
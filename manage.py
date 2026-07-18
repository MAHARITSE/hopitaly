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
  - AttributeError: type object 'BuiltinImporter' has no attribute 'find_module'  (Python 3.12+)
  - ModuleNotFoundError: No module named 'cgi'  (Python 3.13+)
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

# 4b. Patch find_module() on the import machinery (removed in Python 3.12+).
#     Django 1.6's django.utils.module_loading.module_has_submodule() calls
#     finder.find_module(...) on every entry of sys.meta_path (BuiltinImporter,
#     FrozenImporter, PathFinder) and on sys.path_importer_cache finders
#     (FileFinder) - this is hit by admin.autodiscover() on every request
#     setup. PEP 451 replaced find_module() with find_spec() back in Python
#     3.4, and the legacy aliases were finally deleted in Python 3.12, which
#     causes:
#       AttributeError: type object 'BuiltinImporter' has no attribute 'find_module'
#     We re-add thin wrappers that delegate to find_spec().
try:
    from importlib import machinery as _import_machinery

    def _find_module_shim(self, fullname, path=None):
        """Delegate Django 1.6's find_module() to find_spec() (PEP 451)."""
        find_spec = getattr(self, 'find_spec', None)
        if find_spec is None:
            return None
        try:
            spec = find_spec(fullname, path)
        except TypeError:
            # FileFinder.find_spec() takes only (fullname).
            spec = find_spec(fullname)
        if spec is None or getattr(spec, 'loader', None) is None:
            return None
        return spec.loader

    def _patch_finder(finder):
        if not hasattr(finder, 'find_module'):
            try:
                finder.find_module = _find_module_shim
            except Exception:
                pass

    # a) Class-level meta path finders (BuiltinImporter, FrozenImporter,
    #    PathFinder) - on Python <= 3.11 they still have find_module natively,
    #    so this only patches the Python 3.12+ case.
    for _meta_finder in (_import_machinery.BuiltinImporter,
                         _import_machinery.FrozenImporter,
                         _import_machinery.PathFinder):
        _patch_finder(_meta_finder)

    # b) Any *instances* already registered on sys.meta_path. setuptools'
    #    _distutils_hack.DistutilsMetaFinder is added here and ALSO lacks
    #    find_module() on modern Python - Django 1.6 iterates sys.meta_path
    #    directly, so it must be patched too.
    for _finder in list(getattr(sys, 'meta_path', [])):
        _patch_finder(_finder)

    # c) FileFinder is instantiated per sys.path entry (instance level).
    _patch_finder(_import_machinery.FileFinder)
except Exception:
    pass

# 5. Patch cgi module (completely removed in Python 3.13+)
#    Django 1.6's http/multipartparser.py does 'import cgi' and uses
#    cgi.valid_boundary(); templates.py uses cgi.parse_header().
try:
    import cgi
    # cgi still exists (Python < 3.13), nothing to do
except ImportError:
    import re as _re

    class _CgiShim:
        """Minimal cgi module shim for Django 1.6.5 compatibility."""

        @staticmethod
        def valid_boundary(s):
            """Validate a multipart boundary string (RFC 2046)."""
            if isinstance(s, bytes):
                pattern = b"^[ -~]{0,200}[!-~]$"
            else:
                pattern = "^[ -~]{0,200}[!-~]$"
            return _re.match(pattern, s)

        @staticmethod
        def parse_header(line):
            """Parse a Content-type-like header into (main_value, params_dict)."""
            parts = _cgi_parseparam(';' + line)
            key = next(parts)
            pdict = {}
            for p in parts:
                i = p.find('=')
                if i >= 0:
                    name = p[:i].strip().lower()
                    value = p[i+1:].strip()
                    if len(value) >= 2 and value[0] == value[-1] == '"':
                        value = value[1:-1]
                        value = value.replace('\\\\', '\\').replace('\\"', '"')
                    pdict[name] = value
            return key, pdict

    def _cgi_parseparam(s):
        """Split param string by semicolons, respecting quoted strings."""
        while s[:1] == ';':
            s = s[1:]
            end = s.find(';')
            while end > 0 and (s.count('"', 0, end) - s.count('\\"', 0, end)) % 2:
                end = s.find(';', end + 1)
            if end < 0:
                end = len(s)
            f = s[:end]
            yield f.strip()
            s = s[end:]

    cgi = _CgiShim()
    sys.modules['cgi'] = cgi

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
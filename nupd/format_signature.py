import inspect
import re
import types


def _formatannotation(annotation, base_module=None, *, quote_annotation_strings=True):
    if not quote_annotation_strings and isinstance(annotation, str):
        return annotation
    if getattr(annotation, "__module__", None) == "typing":

        def repl(match):
            text = match.group()
            return text.removeprefix("typing.")

        return re.sub(r"[\w\.]+", repl, repr(annotation))
    if isinstance(annotation, types.GenericAlias):
        return str(annotation)
    if isinstance(annotation, type):
        if annotation.__module__ in ("builtins", base_module):
            return annotation.__qualname__
        return annotation.__module__ + "." + annotation.__qualname__
    return repr(annotation)


def _param_format(self, *, quote_annotation_strings=True):
    kind = self.kind
    formatted = self._name

    # Add annotation and default value
    if self._annotation is not self.empty:
        annotation = _formatannotation(
            self._annotation, quote_annotation_strings=quote_annotation_strings
        )
        formatted = "{}: {}".format(formatted, annotation)

    if self._default is not self.empty:
        if self._annotation is not self.empty:
            formatted = "{} = {}".format(formatted, repr(self._default))
        else:
            formatted = "{}={}".format(formatted, repr(self._default))

    if kind == inspect.Parameter.VAR_POSITIONAL:
        formatted = "*" + formatted
    elif kind == inspect.Parameter.VAR_KEYWORD:
        formatted = "**" + formatted

    return formatted


def format_signature(
    self: inspect.Signature,
    *,
    max_width: int = None,
    quote_annotation_strings: bool = True,
):
    """Create a string representation of the Signature object.

    If *max_width* integer is passed,
    signature will try to fit into the *max_width*.
    If signature is longer than *max_width*,
    all parameters will be on separate lines.

    If *quote_annotation_strings* is False, annotations
    in the signature are displayed without opening and closing quotation
    marks. This is useful when the signature was created with the
    STRING format or when ``from __future__ import annotations`` was used.
    """
    result = []
    render_pos_only_separator = False
    render_kw_only_separator = True
    for param in self.parameters.values():
        formatted = _param_format(
            param, quote_annotation_strings=quote_annotation_strings
        )

        kind = param.kind

        if kind == inspect.Parameter.POSITIONAL_ONLY:
            render_pos_only_separator = True
        elif render_pos_only_separator:
            # It's not a positional-only parameter, and the flag
            # is set to 'True' (there were pos-only params before.)
            result.append("/")
            render_pos_only_separator = False

        if kind == inspect.Parameter.VAR_POSITIONAL:
            # OK, we have an '*args'-like parameter, so we won't need
            # a '*' to separate keyword-only arguments
            render_kw_only_separator = False
        elif kind == inspect.Parameter.KEYWORD_ONLY and render_kw_only_separator:
            # We have a keyword-only parameter to render and we haven't
            # rendered an '*args'-like parameter before, so add a '*'
            # separator to the parameters list ("foo(arg1, *, arg2)" case)
            result.append("*")
            # This condition should be only triggered once, so
            # reset the flag
            render_kw_only_separator = False

        result.append(formatted)

    if render_pos_only_separator:
        # There were only positional-only parameters, hence the
        # flag was not reset to 'False'
        result.append("/")

    rendered = "({})".format(", ".join(result))
    if max_width is not None and len(rendered) > max_width:
        rendered = "(\n    {}\n)".format(",\n    ".join(result))

    if self.return_annotation is not self.empty:
        anno = _formatannotation(
            self.return_annotation, quote_annotation_strings=quote_annotation_strings
        )
        rendered += " -> {}".format(anno)

    return rendered

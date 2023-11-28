from .mixins import CodeLinterMixin

from ..interface import CodeLinter


class JavascriptCodeLinter(CodeLinterMixin, CodeLinter):
    id = 'javascript'
    language_extension='js'
    linters='eslint'

    unnecessary_code = [
        'no-unused-vars',
    ]

from .mixins import CodeLinterMixin

from ..interface import CodeLinter


class PythonCodeLinter(CodeLinterMixin, CodeLinter):
    id = 'python'
    language_extension='py'
    linters='pylint'

    unnecessary_code = [
        'W0611',
        'W0612',
        'W0613',
        'W0614',
    ]
    
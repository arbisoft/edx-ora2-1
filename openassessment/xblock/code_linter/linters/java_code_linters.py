from .mixins import CodeLinterMixin

from ..interface import CodeLinter


class JavaCodeLinter(CodeLinterMixin, CodeLinter):
    id = 'java'
    language_extension='java'
    linters='pmd'

    unnecessary_code = [
        'UnnecessaryImport',
        'UnnecessaryLocalBeforeReturn',
        'UnnecessaryReturn',
        'UnusedAssignment',
        'UnusedFormalParameter',
        'UnusedLocalVariable',
        'UnusedPrivateMethod',
        'UnusedPrivateField',
    ]

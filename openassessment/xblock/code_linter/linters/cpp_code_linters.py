from .mixins import CodeLinterMixin

from ..interface import CodeLinter


class JavaCodeLinter(CodeLinterMixin, CodeLinter):
    id = 'cpp'
    language_extension='cpp'
    linters='cppcheck'

    unnecessary_code = [
        'unusedPrivateFunction',
        'unusedFunction',
        'unusedVariable',
        'unusedAllocatedMemory',
        'unreadVariable',
        'unassignedVariable',
        'unusedStructMember',
        'unusedLabel',
    ]

from .mixins import ScriptedLanguageExecutorMixin

from ..interface import CodeExecutor


class PythonCodeExecutor(ScriptedLanguageExecutorMixin, CodeExecutor):
    docker_image = 'litmustest/code-executor-python:3.12'
    language = 'python'
    version = '3.12'
    display_name = 'Python 3.12'

    id = CodeExecutor.create_id('python', '3.12')

    SOURCE_FILE_NAME_TEMPLATE = '{name}.py'
    RUN_COMMAND_STDIN_INPUT_TEMPLATE = 'python3 {source_file}'
    RUN_COMMAND_FILE_INPUT_TEMPLATE = 'python3 {source_file} {input_file}'

class PythonCodeExecutorML(ScriptedLanguageExecutorMixin, CodeExecutor):
    docker_image = 'litmustest/code-executor-python-ml:3.12'
    language = 'python-ml'
    version = '3.12'
    display_name = 'Python 3.12 ML/Data'

    id = CodeExecutor.create_id('python-ml', '3.12')

    SOURCE_FILE_NAME_TEMPLATE = '{name}.py'
    RUN_COMMAND_STDIN_INPUT_TEMPLATE = 'python3 {source_file}'
    RUN_COMMAND_FILE_INPUT_TEMPLATE = 'python3 {source_file} {input_file}'

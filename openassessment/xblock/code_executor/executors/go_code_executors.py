from .mixins import CompiledLanguageExecutorMixin

from ..interface import CodeExecutor


class GoCodeExecutor(CompiledLanguageExecutorMixin, CodeExecutor):
    docker_image = 'litmustest/code-executor-golang:1.25.1-bookworm'
    language = 'go'
    version = 'go-1.25.1'
    display_name = 'Go 1.25.1'

    id = CodeExecutor.create_id('go', 'go-1.25.1')

    SOURCE_FILE_NAME_TEMPLATE = '{name}.go'
    EXECUTABLE_FILE_NAME_TEMPLATE = '{name}'
    COMPILE_COMMAND_TEMPLATE = 'go build -o {executable_file} {source_file}'
    RUN_COMMAND_STDIN_INPUT_TEMPLATE = './{executable_file}'
    RUN_COMMAND_FILE_INPUT_TEMPLATE = './{executable_file} {input_file}'

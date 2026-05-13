from .mixins import ScriptedLanguageExecutorMixin

from ..interface import CodeExecutor


class AlpineTextExecutor(ScriptedLanguageExecutorMixin, CodeExecutor):
    docker_image = 'litmustest/text-executor-alpine:3.21'
    language = 'text'
    version = 'alpine-3.21'
    display_name = 'Text Paragraph'

    id = CodeExecutor.create_id('text', 'alpine-3.21')

    SOURCE_FILE_NAME_TEMPLATE = '{name}.txt'
    RUN_COMMAND_STDIN_INPUT_TEMPLATE = 'cat {source_file}'
    RUN_COMMAND_FILE_INPUT_TEMPLATE = 'cat {source_file}'

from .mixins import ScriptedLanguageExecutorMixin

from ..interface import CodeExecutor


class DotnetCodeExecutor(ScriptedLanguageExecutorMixin, CodeExecutor):
    docker_image = 'litmustest/code-executor-dotnet-sqlite:8.0'
    language = 'dotnet'
    version = '8.0'
    display_name = 'Dotnet 8.0'

    id = CodeExecutor.create_id('dotnet', '8.0')

    SOURCE_FILE_NAME_TEMPLATE = 'Application/{name}.cs'
    RUN_COMMAND_STDIN_INPUT_TEMPLATE = 'dotnet run {source_file} --project Application'
    RUN_COMMAND_FILE_INPUT_TEMPLATE = 'dotnet run {source_file} {input_file} --project Application'

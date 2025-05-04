from .mixins import CompiledLanguageExecutorMixin

from ..interface import CodeExecutor


class KotlinCodeExecutor(CompiledLanguageExecutorMixin, CodeExecutor):
    docker_image = 'litmustest/code-executor-kotlin:1.9.23'
    language = 'kotlin'
    version = '1.9.23'
    display_name = 'Kotlin 1.9.23'

    id = CodeExecutor.create_id('kotlin', '1.9.23')

    SOURCE_FILE_NAME_TEMPLATE = 'Main.kt'
    EXECUTABLE_FILE_NAME_TEMPLATE = 'MainKt'
    COMPILE_COMMAND_TEMPLATE = 'kotlinc -Xmx512m -Xms128m {source_file}'
    RUN_COMMAND_STDIN_INPUT_TEMPLATE = 'kotlin $JAVA_OPTS {executable_file}'
    RUN_COMMAND_FILE_INPUT_TEMPLATE = 'kotlin $JAVA_OPTS {executable_file} {input_file}'
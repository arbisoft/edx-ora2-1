from .mixins import CompiledLanguageExecutorMixin

from ..interface import CodeExecutor


class SwiftCodeExecutor(CompiledLanguageExecutorMixin, CodeExecutor):
    docker_image = 'litmustest/code-executor-swift-sqlite:6.0.3-amazonlinux2'
    language = 'swift'
    version = '6.0.3-amazonlinux2'
    display_name = 'Swift 6.0.3'

    id = CodeExecutor.create_id('swift', '6.0.3-amazonlinux2')

    SOURCE_FILE_NAME_TEMPLATE = 'main.swift'
    EXECUTABLE_FILE_NAME_TEMPLATE = 'main' 
    COMPILE_COMMAND_TEMPLATE = 'swiftc -I /usr/local/include {source_file} -o {executable_file}'
    RUN_COMMAND_STDIN_INPUT_TEMPLATE = './{executable_file}'
    RUN_COMMAND_FILE_INPUT_TEMPLATE = './{executable_file} {input_file}'
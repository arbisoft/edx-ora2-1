"""
PHP Code Executor Module

This module provides a code executor for PHP scripts using the EpicBox container system.
The executor supports PHP 8.3.3 and handles both stdin and file-based input methods.
"""

from .mixins import ScriptedLanguageExecutorMixin

from ..interface import CodeExecutor


class PhpCodeExecutor(ScriptedLanguageExecutorMixin, CodeExecutor):
    """
    Code executor for PHP scripts.
    
    This executor runs PHP code using the stepik/epicbox-php:8.3.3 Docker image.
    It supports both stdin input and file input methods for script execution.
    
    Attributes:
        docker_image (str): Docker image used for PHP code execution
        language (str): Programming language identifier
        version (str): PHP version
        display_name (str): Human-readable name for the executor
        id (str): Unique identifier for this executor
        SOURCE_FILE_NAME_TEMPLATE (str): Template for PHP source file naming
        RUN_COMMAND_STDIN_INPUT_TEMPLATE (str): Command template for stdin input
        RUN_COMMAND_FILE_INPUT_TEMPLATE (str): Command template for file input
    
    Example:
        >>> executor = PhpCodeExecutor()
        >>> result = executor.execute(code="<?php echo 'Hello World'; ?>")
    """
    docker_image = 'stepik/epicbox-php:8.3.3'
    language = 'php'
    version = '8.3.3'
    display_name = 'PHP 8.3.3'

    id = CodeExecutor.create_id('php', '8.3.3')

    SOURCE_FILE_NAME_TEMPLATE = '{name}.php'
    RUN_COMMAND_STDIN_INPUT_TEMPLATE = 'php {source_file}'
    RUN_COMMAND_FILE_INPUT_TEMPLATE = 'php {source_file} {input_file}'

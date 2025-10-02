"""
.NET Code Executor Module

This module provides a code executor for .NET/C# programs using the dotnet CLI.
The executor compiles and runs C# code in a sandboxed Docker environment using epicbox.
"""

from .mixins import CompiledLanguageExecutorMixin

from ..interface import CodeExecutor


class DotnetCodeExecutor(CompiledLanguageExecutorMixin, CodeExecutor):
    """
    Code executor for .NET 8.0 C# programs.

    This executor runs C# code using the dotnet CLI in a sandboxed Docker container.
    It uses a compiled language execution model with two phases:

    1. Compilation Phase: Compiles the C# source code using 'dotnet build'
       - User source code is copied to a pre-configured Application project directory
       - Build output is redirected to stderr (>&2) for proper error capture
       - Compilation errors are caught and raised as CodeCompilationError

    2. Execution Phase: Runs the compiled DLL using 'dotnet'
       - Executes the built Application.dll from the output directory
       - Program stdout/stderr are handled separately for accurate output capture

    The Docker image contains a pre-configured .NET project structure with necessary
    dependencies including SQLite support.

    Attributes:
        docker_image (str): Docker image containing .NET 8.0 SDK and runtime
        language (str): Programming language identifier ('dotnet')
        version (str): .NET version ('8.0')
        display_name (str): Human-readable name shown in UI
        id (str): Unique identifier for this executor
        SOURCE_FILE_NAME_TEMPLATE (str): Name for C# source file (Program.cs)
        EXECUTABLE_FILE_NAME_TEMPLATE (str): Name for compiled executable (Application)
        COMPILE_COMMAND_TEMPLATE (str): Command to compile the C# code
        RUN_COMMAND_STDIN_INPUT_TEMPLATE (str): Command to run with stdin input
        RUN_COMMAND_FILE_INPUT_TEMPLATE (str): Command to run with file input

    Example:
        >>> executor = DotnetCodeExecutor(source_code='Console.WriteLine("Hello");')
        >>> with executor:
        ...     result = executor.run_input('')
        >>> print(result['stdout'].decode('utf-8'))
        Hello

    Note:
        The .NET SDK writes all output (including compilation errors) to stdout by default.
        This executor redirects build output to stderr (>&2) to ensure compilation errors
        are properly captured by the exception handling mechanism in the mixin.
    """
    docker_image = 'litmustest/code-executor-dotnet-sqlite:8.0'
    language = 'dotnet'
    version = '8.0'
    display_name = 'Dotnet 8.0'

    id = CodeExecutor.create_id('dotnet', '8.0')

    SOURCE_FILE_NAME_TEMPLATE = 'Program.cs'
    EXECUTABLE_FILE_NAME_TEMPLATE = 'Application'

    # Copy the user's source code to the existing Application project and build it
    COMPILE_COMMAND_TEMPLATE = (
        'cp {source_file} Application/Program.cs && '
        'cd Application && '
        'dotnet build -o ../output >&2'
    )

    # Run the built DLL - note we stay in the working directory, not cd to output
    RUN_COMMAND_STDIN_INPUT_TEMPLATE = 'dotnet output/Application.dll'
    RUN_COMMAND_FILE_INPUT_TEMPLATE = 'dotnet output/Application.dll {input_file}'

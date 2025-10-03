from .mixins import CompiledLanguageExecutorMixin

from ..interface import CodeExecutor


class DotnetCodeExecutor(CompiledLanguageExecutorMixin, CodeExecutor):
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
        'dotnet build -o ../output'
    )
    
    # Run the built DLL - note we stay in the working directory, not cd to output
    RUN_COMMAND_STDIN_INPUT_TEMPLATE = 'dotnet output/Application.dll'
    RUN_COMMAND_FILE_INPUT_TEMPLATE = 'dotnet output/Application.dll {input_file}'

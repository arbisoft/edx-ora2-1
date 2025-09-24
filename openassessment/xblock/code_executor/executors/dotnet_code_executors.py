from .mixins import CompiledLanguageExecutorMixin

from ..interface import CodeExecutor


class DotnetCodeExecutor(CompiledLanguageExecutorMixin, CodeExecutor):
    docker_image = 'litmustest/code-executor-dotnet-sqlite:8.0'
    language = 'dotnet'
    version = '8.0'
    display_name = 'Dotnet 8.0'

    id = CodeExecutor.create_id('dotnet', '8.0')

    SOURCE_FILE_NAME_TEMPLATE = 'Program.cs'
    EXECUTABLE_FILE_NAME_TEMPLATE = 'Application'  # Project name for dotnet run
    
    # Create a temporary project and copy the source code to Program.cs
    COMPILE_COMMAND_TEMPLATE = (
        'mkdir -p temp_project && '
        'cp {source_file} temp_project/Program.cs && '
        'cd temp_project && '
        'dotnet new console --force && '
        'dotnet add package Microsoft.Data.Sqlite --version 8.0.0 && '
        'cp Program.cs.bak Program.cs 2>/dev/null || cp Program.cs Program.cs.bak && '
        'cp ../Program.cs Program.cs && '
        'dotnet build -o ../output'
    )
    
    RUN_COMMAND_STDIN_INPUT_TEMPLATE = 'cd output && dotnet *.dll'
    RUN_COMMAND_FILE_INPUT_TEMPLATE = 'cd output && dotnet *.dll {input_file}'

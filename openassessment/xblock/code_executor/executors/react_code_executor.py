from .mixins import ScriptedLanguageExecutorMixin

from ..interface import CodeExecutor


class ReactCodeExecutorV24(ScriptedLanguageExecutorMixin, CodeExecutor):
    docker_image = 'litmustest/react-code-executor:node-24-slim'
    language = 'reactjs'
    version = 'reactjs-19-node-24'
    display_name = 'React (ReactJS 19 + NodeJS 24 + tsx)'

    id = CodeExecutor.create_id('reactjs', 'reactjs-19-node-24')

    SOURCE_FILE_NAME_TEMPLATE = 'solution.jsx'
    RUN_COMMAND_STDIN_INPUT_TEMPLATE = 'tsx test-runner.jsx'
    RUN_COMMAND_FILE_INPUT_TEMPLATE = 'tsx test-runner.jsx {input_file}'

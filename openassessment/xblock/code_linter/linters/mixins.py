import docker

import os
import json
from abc import ABC
from typing import Dict, List
from uuid import uuid4

import logging
logger = logging.getLogger(__name__)

class CodeLinterMixin(ABC):

    __SECRET_DATA_DIR__ = '/rubricdata/'

    language_extension=''
    linters=''

    SOURCE_FILE_WITH_PATH = '{directory}/{name}.{extension}'
    RUN_COMMAND_TEMPLATE = 'trunk check {source_file} --filter={linters} --output=json'

    @classmethod
    def get_config(cls) -> dict:
        return { 'id': cls.id }

    def __init__(
        self,
        source_code: str,
        **kwargs
    ) -> None:
        self.source_code=source_code
        self.source_code_with_path=self.SOURCE_FILE_WITH_PATH.format(           
            name=uuid4(),
            directory=self.__SECRET_DATA_DIR__,
            extension=self.language_extension,
        )

    def __enter__(self):
        self.write_code_file()

    def __exit__(self, exc_type, exc_value, exc_tb):
        if os.path.isfile(self.source_code_with_path):
            os.remove(self.source_code_with_path)

    def run_linter(self):
        client = docker.from_env()
        container = client.containers.get('edx.devstack.rubric_automation')
        exec_response = container.exec_run(self.RUN_COMMAND_TEMPLATE.format(
            source_file=self.source_code_with_path,
            linters=self.linters
        ))
        result = json.loads(exec_response.output.decode('utf-8'))
        return self.run_rubrics(result)

    def run_rubrics(self, output):
        result = {
            'Unnecessary Code': 0,
        }
        for issue in output.get('issues'):
            if issue.get('code') is not None and issue.get('code') in self.unnecessary_code:
                result['Unnecessary Code'] = result['Unnecessary Code'] + 1
        
        return result

    def write_code_file(self):
        f = open(self.source_code_with_path, 'w')
        f.write(self.source_code)
        f.close()

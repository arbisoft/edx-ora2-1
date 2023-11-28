from .config import get_all_code_linter_configs
from .interface import CodeLinter

import logging
logger = logging.getLogger(__name__)

CODE_LINTER_CONFIGS = get_all_code_linter_configs()
CODE_LINTER_CONFIG_ID_MAP = {config['id']: config for config in CODE_LINTER_CONFIGS}


class CodeLinterFactory:
    @staticmethod
    def get_code_linter(
        code_linter_id: str,
        source_code: str,
        **kwargs
    ) -> CodeLinter:
        config = CODE_LINTER_CONFIG_ID_MAP.get(code_linter_id)
        if not config:
            raise Exception('No linter found for id')
        klass = config.get('class')
        if klass:
            return klass(source_code=source_code, **kwargs)

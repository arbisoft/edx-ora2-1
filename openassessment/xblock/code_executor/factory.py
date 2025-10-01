from typing import Dict, List

import epicbox

from .constants import DEFAULT_LIMITS, LIMITS
from .config import get_all_code_executor_configs, get_all_epicbox_profiles
from .interface import CodeExecutor


epicbox.configure(get_all_epicbox_profiles())


CODE_EXECUTOR_CONFIGS = get_all_code_executor_configs()
CODE_EXECUTOR_CONFIG_ID_MAP = {config['id']: config for config in CODE_EXECUTOR_CONFIGS}


class CodeExecutorFactory:
    @staticmethod
    def get_code_executor(
        code_executor_id: str,
        source_code: str,
        files: List[Dict[str, bytes]] = [],
        limits: Dict[str, int] = None,
        **kwargs
    ) -> CodeExecutor:
        config = CODE_EXECUTOR_CONFIG_ID_MAP.get(code_executor_id)
        if not config:
            raise Exception('No executor found for id')

        # Use language-specific limits if available, otherwise use provided limits or DEFAULT_LIMITS
        if limits is None:
            limits = LIMITS.get(code_executor_id, DEFAULT_LIMITS)

        klass = config.get('class')
        if klass:
            return klass(source_code=source_code, files=files, limits=limits, **kwargs)

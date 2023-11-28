from abc import ABC, abstractmethod

class CodeLinter(ABC):
    """
    Interface for all types of code executors. Code executors must have this class as one of their
    ancestor classes, otherwise the code executor will not be automatically registered.
    """

    @classmethod
    @abstractmethod
    def get_config(cls) -> dict:
        """
        Returns the config for this linter. The structure is as follows.
        
            {
                'id': 'id',
                'language': '',
            }

        Returns:
            dict: config object.
        """
        pass

    @abstractmethod
    def __init__(
        self,
        source_code: str,
        *args,
        **kwargs
    ) -> None:
        pass

    def __enter__(self):
        pass

    def __exit__(self, exc_type, exc_value, exc_tb):
        pass

    @abstractmethod
    def run_linter(self, name: str) -> dict:
        pass

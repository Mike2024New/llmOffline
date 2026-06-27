from infrastructure.path_utils import FlatJsonManager
import config


class PromptManager:
    """
    Прослойка для управления базой промптов
    """

    def __init__(self):
        self.prompt_manager = FlatJsonManager(prompt_file_path=config.RPOMPT_JSON_PATH)

    def add(self, name: str, prompt: str) -> None:
        self.prompt_manager.add(key=name, value=prompt)

    def remove(self, name: str) -> None:
        self.prompt_manager.remove(key=name)

    def get(self, name: str) -> str:
        return self.prompt_manager.get(key=name, default=None)

    def all(self) -> dict[str, str]:
        return self.prompt_manager.data()

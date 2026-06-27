import config
from core.main import Engine
from core.functions import get_available_models_list
from core.prompt_manager import PromptManager

__all__ = [
    'Engine',  # проброс движка для внешних компонентов
    'get_available_models_list',  # получение списка моделей
    'PromptManager',  # управление промптами
]

# создание базового промпта
prompt_manager = PromptManager()
prompt_manager.add(name='base_prompt', prompt=config.settings_manager.settings_model.default_system_prompt)

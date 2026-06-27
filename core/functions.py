import config
from llama_cpp import llama_log_set, llama_log_callback
from infrastructure.http_clients import adpater_download_from_hf

__all__ = [
    'log_shut_up',
    'get_available_models_list',
]


# подавление логов llama
@llama_log_callback
def silence_logs(_level, _message, _user_data):
    pass


def log_shut_up():
    llama_log_set(silence_logs, None)  # noqa


def download_model(model_name: str) -> None:
    """Загрузка модели с HF (на основании config.models_map)"""
    adpater_download_from_hf(
        models_list=config.models_map,
        download_dir=config.MODELS_DIR,
        model_name=model_name,
        replace_file=True,
        message_bus_add=config.message_bus_add,
        wait_for=True,
        print_progress=True,
        nested_folder=False,
    )


def get_available_models_list() -> list[str]:
    """
    Получить список моделей доступных пользователю, на основании схемы config.models_map
    """
    available_llm_models_list = []
    for repository in config.models_map:
        for model in config.models_map[repository]:
            available_llm_models_list.append(model)
    return available_llm_models_list


def get_model_file_name(model_name: str) -> str:
    """
    Получение названия файла модели для составления пути к ней
    """
    for repository in config.models_map:
        for model in config.models_map[repository]:
            if model_name == model:
                # для текущего маппинга 0 индекс всегда (1 файл 1 модель)
                return config.models_map[repository][model][0]
    raise RuntimeError(f'Модель {model_name} не найдена, доступны {get_available_models_list()}')

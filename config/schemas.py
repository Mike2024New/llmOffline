from pydantic import BaseModel, Field, RootModel

__all__ = [
    'llm_settings', 'SettingsService',
    'models_schema',  # схема моделей для загрузки с HF, и работы с ними в core
]

# схема url моделей доступных на hugging-face
hugging_face_llm_models_map = {
    'lmstudio-community': {
        'gemma-3-4b-it-GGUF': ["gemma-3-4b-it-Q4_K_M.gguf"],
        'gemma-3-12b-it-GGUF': ["gemma-3-12b-it-Q4_K_M.gguf"],
    },
}


class ModelsMap(RootModel[dict[str, dict[str, list[str]]]]):
    """Карта моделей"""


# карта используемых моделей
models_schema = ModelsMap.model_validate({
    'lmstudio-community': {  # репозтироий
        'gemma-3-4b-it-GGUF': ["gemma-3-4b-it-Q4_K_M.gguf"],  # название модели : название файла (как на url)
        'gemma-3-12b-it-GGUF': ["gemma-3-12b-it-Q4_K_M.gguf"],
    },
})


class SettingsModel(BaseModel):
    n_ctx: int = Field(
        default=1024,
        description='Длина контекста модели, чем больше тем позже модель забудет первые сообщения (ест оперативную память)',
        ge=0, le=256000,
    )
    use_mmap: bool = Field(
        default=True,
        description='True Использовать виртуальную память? Медленнее (но не переполняет RAM), или False загрузить в RAM (быстрее)'
    )
    model_log: bool = Field(default=False, description='Показывать логи модели(llama-cpp)?')
    max_tokens: int = Field(
        default=512,
        description='Длина ответа модели (ест контекст).',
        ge=0, le=64000,
    )
    temperature: float = Field(
        default=0.5,
        description='Творческий режим модели, 0.1 без импровизации кратко по существу, чем больше тем более размытый.',
        ge=0, le=10,
    )
    history_messages_limit: int = Field(default=10, description='Ограничение длины сообщений в памяти модели.')
    processor_power_percentage: int = Field(
        default=100,
        description='Использовать мощность процессора в % (пропорциональное вычисление количества ядер)',
        ge=0, le=100,
    )
    default_system_prompt: str = Field(
        default='Привет! Давай просто пообщаемся на разные темы, отвечай кратко без маркдаунов и разметки.'
    )


class SettingsService(BaseModel):
    settings_model: SettingsModel
    local_files_only: bool = Field(
        default=True,
        description='Запретить выходить в web (не доступно скачивание моделей).'
    )


llm_settings = SettingsService(settings_model=SettingsModel())

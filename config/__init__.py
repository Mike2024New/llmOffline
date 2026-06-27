import platform, sys
from pathlib import Path
import uuid
from infrastructure.other import ShutUpLogs
from infrastructure.message_bus import message_bus_factory_v2, MessagePrintSettings, FileLogSettings
from infrastructure.settings_manager import get_settings_manager
from config.schemas import llm_settings, models_schema

__all__ = [
    'ROOT_DIR', 'MODELS_DIR',
    'shut_up',  # успокоить логи
    'message_bus_add', 'message_bus_settings',  # шина сообщений (логирование, сигналы компонента)
    'settings_manager',  # настройки приложения (settings.json)
    'models_map',  # карта моделей для загрузки с HF, и работе с ними в core
]

IS_WINDOWS = 'windows' in platform.system().lower()

# для сборщика (pyinstaller)
EXE_MODE = getattr(sys, 'frozen', False)

# определение корневой точки приложения
ROOT_DIR = Path(sys.executable).parent if EXE_MODE else Path(__file__).parent.parent

# директории с ресурсами
RESOURCES_DIR = ROOT_DIR / 'resources'
MODELS_DIR = RESOURCES_DIR / 'models'
MODELS_DIR.mkdir(parents=True, exist_ok=True)

# папка с логами
LOGS_FILE_PATH = ROOT_DIR / 'logs' / 'log.jsonl'
LOGS_FILE_PATH.parent.mkdir(exist_ok=True, parents=True)

# путь к файлу json хранящему промпты
RPOMPT_JSON_PATH = ROOT_DIR / 'prompts.json'

# шина сообщений
message_bus_add, message_bus_settings = message_bus_factory_v2(
    component_id=str(uuid.uuid4())[:8],
    component_name='LLM',
    print_message=True,
    # подключение сообщений
    message_print_settings=MessagePrintSettings(
        print_date=True,
        raw_message=False,
        ignore_levels=[],
        ignore_levels_invers=False,
    ),
    # подключение логирования в файл
    file_log_json_path=LOGS_FILE_PATH,
    file_log_settings=FileLogSettings(
        max_files=10,
        max_size_mb=10,
        rotation_disable=False,
    )
)

# загрузка настроек приложения
settings_manager = get_settings_manager(
    json_file_path=Path(ROOT_DIR / 'settings.json'),
    settings_model=llm_settings,
).settings

# загрузка схемы моделей -> пробрасывается чистый словарь
models_map = get_settings_manager(
    json_file_path=Path(ROOT_DIR / 'models_map.json'),
    settings_model=models_schema,
).settings.root

# ===========================================================
# НАСТРОЙКИ
# ===========================================================
# подавить встроенные логи приложений?
shut_up = ShutUpLogs(off=False)
# печатать логи шины сообщений в консоль? (enable_print / disable_print)
message_bus_settings.enable_print()

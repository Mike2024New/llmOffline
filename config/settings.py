import config
from infrastructure.builder import BuildParameters
from pathlib import Path

# настройки сборки приложения (похватываются в cli.py)
build_settings = BuildParameters(
    name=config.APP_NAME,
    entry_point_path=config.ROOT_DIR / 'cli.py',
    one_file=True,
    create_resources_symlink=False,
    open_folder=True,
)

# добавление бинарных файлов:
build_settings.add_binary.extend([
    Path('llama_cpp') / 'lib',  # пути к llama .dll
])

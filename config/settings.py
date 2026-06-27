import config
from infrastructure.builder import BuildParameters
from pathlib import Path

# настройки сборки приложения (похватываются в cli.py)
build_settings = BuildParameters(
    name='llm',
    entry_point_path=config.ROOT_DIR / 'cli.py',
    one_file=True,
    create_resources_symlink=False,
    open_folder=True,
    add_binary=[Path('llama_cpp') / 'lib'],
)

import config
import typer
from rich import print
from core import Engine, get_available_models_list, PromptManager
from pathlib import Path

prompt_manager = PromptManager()

app = typer.Typer(
    no_args_is_help=True,
    # если пользователь дал команду без аргументов то не падать с ошибкой а показать справку
    rich_markup_mode='rich',
    # добавить rich панели (группировка комманд по заголовкам)
    add_completion=False,  # убрать блок option в всплывающем меню
)


@app.callback()
def main():
    """CLI интерфейс"""


@app.command()
def folder():
    """Открыть домашнюю папку приложения"""
    from infrastructure.path_utils.open_folder import open_folder
    open_folder(config.ROOT_DIR)


# <специфичные параметры модуля >

@app.command()
def pr_show():
    """
    Просмотр списка промптов (личная библиотека промптов)
    Примеры команд:
        [yellow]pr-show[/yellow]
    """
    prompts_list = prompt_manager.all()
    for prompt in prompts_list:
        print(f'[green]{prompt} : {prompts_list[prompt]}[/green]')


@app.command()
def pr_add(
        prompt_name: str | None = typer.Option(None, '-pn', '--prompt-name'),
        prompt_text: str | None = typer.Option(None, '-pt', '--prompt-text'),
):
    """
    Добавить системный промпт (личная библиотека промптов)
    Параметры (обязательные):
        -pn(--prompt-name) - название промпта
        -pt(--prompt-text) - текст промпта
    Примеры команд:
        [yellow]pr-add -pn "мой промпт 1" -pt "Привет, ты ИИ ассистент, давай просто поговорим"[/yellow]
    """
    if prompt_name is None or prompt_text is None:
        print(f'[red]Промпт не добавлен, должны быть указаны оба параметра (-pn, -pt)[/red]')

    prompt_manager.add(
        name=prompt_name,
        prompt=prompt_text,
    )
    print(f'[green]Промпт `{prompt_name}` добавлен.[/green]')


@app.command()
def pr_remove(
        prompt_name: str | None = typer.Option(None, '-pn', '--prompt-name'),
):
    """
    Добавить системный промпт (личная библиотека промптов)
    Параметры (обязательные):
        -pn(--prompt-name) - название промпта
    Примеры команд:
        [yellow]pr-add -pn "мой промпт 1" [/yellow]
    """
    if prompt_name is None:
        print(f'[red]Для удаление промпта нужно указать его название (-pn)[/red]')

    prompt_manager.remove(
        name=prompt_name,
    )
    print(f'[green]Промпт `{prompt_name}` удален.[/green]')


@app.command()
def models():
    """
    Получение списка доступных моделей, например ['gemma-3-4b-it-GGUF', 'gemma-3-12b-it-GGUF']
    Примеры команд:
        [yellow]models[/yellow]
    """
    models_list = get_available_models_list()
    print(f"[green]{models_list}[/green]")


@app.command()
def chat(
        model_name: str | None = typer.Option(None, '-mn', '--model-name'),
        system_prompt: str | None = typer.Option(None, '-sp', '--sys-prompt'),
):
    """
    Интерактивный чат с моделью.
    Опции:
        -mn (--model-name) - прямое указание модели
        -sp (--sys-prompt) - прямое указание системного промпта
    Примеры команд:
        [yellow]chat[/yellow] - запустится меню с интерактивным выбором модели и промпта а за тем и чат
        [yellow]chat -mn gemma-3-4b-it-GGUF[/yellow] - модель указана, система попросит выбрать промпт
        [yellow]chat -sp "Ты мой AI помощник."[/yellow] - промпт указан система попросит выбрать модель
        [yellow]chat -mn gemma-3-4b-it-GGUF -sp "Ты мой AI помощник."[/yellow] - все параметры указаны
    """
    models_list = get_available_models_list()

    if model_name is None:
        # определение промпта (если её не передали в параметрах)
        [print(f"[cyan]{i}. {model}[/cyan]") for i, model in enumerate(models_list)]
        user_input = input(f'Выберите номер модели:_ ')
        if not user_input.isdigit() or int(user_input) > len(models_list) - 1:
            print(f'[red]Не верно указан индекс модели должно быть число [0:{len(models_list) - 1}].[/red]')

        model_name = models_list[int(user_input)]

    if system_prompt is None:
        # определение промпта (если его не передали в параметрах)
        pr_list = prompt_manager.all()
        pr_list_keys = list(pr_list.keys())
        [print(f"[cyan]{i}. {prompt} -> {pr_list[prompt][:40]}...[/cyan]") for i, prompt in enumerate(pr_list_keys)]
        user_input = input(f'Выберите номер промпта:_ ')
        if not user_input.isdigit() or int(user_input) > len(pr_list_keys) - 1:
            print(f'[red]Не верно указан индекс промпта должно быть число [0:{len(models_list) - 1}].[/red]')
        prompt = pr_list_keys[int(user_input)]
        system_prompt = pr_list[prompt]

    user_input = input(f'Вы согласны на скачивание моделей с HF ( https://huggingface.co/ )? (y/n):_ ')
    consent_to_upload = True if user_input == 'y' else False

    try:
        engine = Engine()
        engine.start(model_name=model_name, system_prompt=system_prompt, consent_to_upload=consent_to_upload)
        engine.interactive_chat()
    except Exception:  # noqa
        pass


# </ специфичные параметры модуля >

# < режим разработчика >
if not config.EXE_MODE:
    @app.command()
    def build(
            name: str | None = typer.Option(None, '-n', '-name'),
            one_file: bool = typer.Option(False, '-oe', '--onefile', flag_value=True),
            entry_path: Path | None = typer.Option(None, '-ep', '--entry_path'),
            create_resources_symlink: bool = typer.Option(False, '-sl', '--sym-link', flag_value=True),
    ):
        """
        [red]~dev [/red]Создание сборки, приложения .exe или .bin [yellow]build[/yellow]
        система определяется автоматически windows/linux
        Опции:
            -n (--name) - название приложения (если не переопределить то взьмется по умолчанию из settings)
            -oe (--onefile) - сборка одним файлом (по умолчанию выключена)
            -sl (--sym-link) - создать симлинк на папку с ресурсами
            -ep (--entry_path) - стартовый скрипт (по умолчанию этот же скрипт cli.py)
        Примеры команд:
            [yellow]build[/yellow]
            [yellow]build -n my-app[/yellow] - указать название приложения
            [yellow]build -oe[/yellow] - сборка одним файлом
            [yellow]build -ep ./main.py[/yellow] - входная точка приложения указанный файл
            [yellow]build -sl[/yellow] - создать симлинк на папку с ресурсами (для разработки)
            [yellow]build -n my-app -oe -ep -s ./main.py[/yellow] - все вместе с указанием точки сборки
        """
        from infrastructure.builder.main import build
        from config.settings import build_settings
        # переопределение опций
        build_settings.name = name if name is not None else build_settings.name
        build_settings.one_file = one_file
        build_settings.create_resources_symlink = create_resources_symlink
        build_settings.entry_point_path = entry_path if entry_path is not None else build_settings.entry_point_path

        build(build_settings)


    @app.command()
    def git_push():
        """
        [red]~dev [/red]Отправка git, с редактированием минорной версии в pyproject.toml, и редактировании блока
        истории в .md (при условии что там есть заголовок [yellow]`## История развития модуля`[/yellow] и в нем написана новость
        вида [yellow]`@new`[/yellow]. В корне проекта должен быть файл .env с переменными GIT_URL=<ваш url>, GIT_BRANCH=<ветка>.
        Примеры команд:
            [yellow]git-push[/yellow]
        """
        from infrastructure.git_client import adapter_git_push_update
        adapter_git_push_update(
            root_dir=config.ROOT_DIR,
            history_header='## История развития модуля',
            history_new_marker='@new',
        )

# </ режим разработчика >

if __name__ == '__main__':
    app()

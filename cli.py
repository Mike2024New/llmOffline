import config
import typer
from rich import print
from infrastructure.cli_utils import get_cli_app, cli_command_execute
from config.settings import build_settings
from core import get_available_models_list, PromptManager, Engine

prompt_manager = PromptManager()

# получение базовых повторяющихся команд
app = get_cli_app(
    name=config.APP_NAME,
    root_dir=config.ROOT_DIR,
    build_settings=build_settings,
    exe_mode=config.EXE_MODE,
    message_bus=config.message_bus_add,
)


@app.command()
def models(ctx: typer.Context):
    """
    Получение списка доступных моделей, например ['gemma-3-4b-it-GGUF', 'gemma-3-12b-it-GGUF']
    Примеры команд:
        [yellow]models[/yellow]
    """

    models_list = cli_command_execute(
        lambda: get_available_models_list(),
        command_name=ctx.command.name,

    )
    print(f"[green]{models_list}[/green]")


@app.command()
def pr_show(ctx: typer.Context):
    """
    Просмотр списка промптов (личная библиотека промптов)
    Примеры команд:
        [yellow]pr-show[/yellow]
    """

    prompts_list = cli_command_execute(
        lambda: prompt_manager.all(),
        command_name=ctx.command.name,

    )

    for prompt in prompts_list:
        print(f'[green]{prompt} : {prompts_list[prompt]}[/green]')


@app.command()
def pr_add(
        ctx: typer.Context,
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

    cli_command_execute(
        lambda: prompt_manager.add(name=prompt_name, prompt=prompt_text, ),
        command_name=ctx.command.name,

    )
    print(f'[green]Промпт `{prompt_name}` добавлен.[/green]')


@app.command()
def pr_remove(
        ctx: typer.Context,
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

    cli_command_execute(
        lambda: prompt_manager.remove(name=prompt_name),
        command_name=ctx.command.name,

    )
    print(f'[green]Промпт `{prompt_name}` удален.[/green]')


@app.command()
def run(
        ctx: typer.Context,
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

    def interactive_chat():
        engine = Engine()
        engine.start(model_name=model_name, system_prompt=system_prompt, consent_to_upload=consent_to_upload)
        engine.interactive_chat()

    cli_command_execute(
        lambda: interactive_chat(),
        command_name=ctx.command.name,
    )


if __name__ == '__main__':
    app()

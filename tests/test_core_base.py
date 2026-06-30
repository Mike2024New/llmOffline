import config
import pytest
from core import Engine
from core import functions


@pytest.fixture(scope='module')
def engine():
    # подмена конфигурации на модель gemma-3-1b
    config.models_map = {'lmstudio-community': {'gemma-3-1b-it-GGUF': ['gemma-3-1b-it-Q4_K_M.gguf']}}
    eng = Engine()
    eng.start(
        model_name='gemma-3-1b-it-GGUF',
        system_prompt='Привет, ты голосовой ассистент.',
        consent_to_upload=True
    )
    return eng


def test_availables_models():
    assert 'gemma-3-1b-it-GGUF' in functions.get_available_models_list(), f'Ошибка отображения списка разрешенных моделей'


# web тест
def test_start_engine(engine):
    answer = engine.ask(prompt='Привет, скажи что нибудь.')
    assert answer is not None
    assert isinstance(answer, str)
    assert answer != ''

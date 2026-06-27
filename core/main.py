import config
import os, uuid, atexit, threading
from time import perf_counter
from llama_cpp import Llama
from core import functions
from config.schemas import SettingsService
from typing import Callable


class Engine:
    def __init__(self):
        self._parameters: SettingsService = config.settings_manager
        self._model: Llama | None = None
        self._messages = []
        self._one_message_mode = False
        self._interrupt_answer = threading.Event()
        atexit.register(self.stop)

    def start(
            self, model_name, system_prompt: str | None = None,
            consent_to_upload: bool = False, one_message_mode: bool = False
    ) -> None:
        """
        Запуск модели, тяжелый метод.
        :param model_name: название модели, например 'gemma-3-4b-it-GGUF'
        :param system_prompt: роль модели, кто она?
        :param consent_to_upload: согласие на то что модель будет загружена с HF. (Важно для оффлайн позиционирования приложения)
        :param one_message_mode: не хранить историю сообщений и работать в режиме вопрос/ответ (например для переводчика на др. язык)
        """
        if self._model:
            return None

        request_id = str(uuid.uuid4())[:8]
        config.message_bus_add(
            request_id=request_id,
            level='start',
            subcomponent='llm',
            message=f'Выполняется загрузка модели {model_name}',
            event='start model loading',
        )

        start = perf_counter()  # начало замера времени
        self._interrupt_answer.clear()  # сброс прерывателя
        self._one_message_mode = one_message_mode  # режим работы модели:  диалог / вопрос-ответ
        system_prompt = system_prompt or self._parameters.settings_model.default_system_prompt

        # проверить что model_name указана существующая (разрешенная модель)
        available_llm_models_list = functions.get_available_models_list()
        if model_name not in available_llm_models_list:
            raise RuntimeError(f'Модель `{model_name}` не найдена, доступны `{available_llm_models_list}`.')

        # определение пути к модели
        model_path = functions.get_model_file_name(model_name)
        model_path = config.MODELS_DIR / model_path

        # скачать модель если она есть в словаре разрешенных моделей, но её ещё нет в resource/models
        if not model_path.exists():
            if consent_to_upload:
                functions.download_model(model_name=model_name)
            else:
                error_msg = f'Загрузка модели не возможна так как не получено соглашение о загрузке модели, нужно передать consent_to_upload.'
                config.message_bus_add(
                    request_id=request_id,
                    level='start',
                    subcomponent='llm',
                    message=error_msg,
                    event='consent error'
                )
                raise RuntimeError(error_msg)

        # Расчёт используемой мощности процессора (например ядер 16 -> 80% используется 12 ядер)
        percent = self._parameters.settings_model.processor_power_percentage
        cpu_count = os.cpu_count()
        cpu_core_used = (cpu_count * percent) // 100
        cpu_core_used = cpu_core_used if cpu_core_used > 0 else 1

        # подавление логов llama
        if not self._parameters.settings_model.model_log:
            functions.log_shut_up()

        # загрузка модели:
        self._model = Llama(
            model_path=str(model_path),
            n_ctx=self._parameters.settings_model.n_ctx,
            n_threads=cpu_core_used,
            use_mmap=self._parameters.settings_model.use_mmap,
            verbose=self._parameters.settings_model.model_log,
        )
        config.message_bus_add(
            request_id=request_id,
            level='start',
            subcomponent='llm',
            message=f'Модель загрузилась за {perf_counter() - start:.2f} сек. Модель `{model_name}`, CPU_CORES: {cpu_core_used}',
            data={
                'cpu_core_used': cpu_core_used,
                'max_tokens': self._parameters.settings_model.max_tokens,
                'temperature': self._parameters.settings_model.temperature,
            }
        )
        # в любом случае добавляется системный промпт
        self._messages.append({'role': 'system', 'content': system_prompt})
        return None

    def _ask_core(self, prompt: str, callback: Callable[[str], ...] = None) -> None:
        """
        Атомарная единица запроса к LLM модели.
        :param prompt: сообщение на которое модель собирается ответить
        :param callback: функция применимая сразу к выдаваему моделью текстом (например стриминг в web)
        None
        """
        if not self._model:
            return None
        response_text = ''
        self._interrupt_answer.clear()
        self._messages.append({'role': 'user', 'content': prompt})
        for chunk in self._model.create_chat_completion(
                messages=self._messages,
                max_tokens=self._parameters.settings_model.max_tokens,
                temperature=self._parameters.settings_model.temperature,
                stream=True
        ):
            if self._interrupt_answer.is_set():
                break
            if "choices" in chunk and len(chunk["choices"]) > 0:
                delta = chunk["choices"][0].get("delta", {})
                if "content" in delta:
                    content = delta["content"]
                    if any(content == '\n' * i for i in range(2, 5)):
                        content = ' '
                    if callback:
                        callback(content)
                    response_text += content

        if response_text:
            if self._one_message_mode:  # очистить историю сообщений (кроме системного промпта)
                self._messages = self._messages[:-1]
            else:  # режим диалога, хранить историю
                self._messages.append({"role": "assistant", "content": response_text})

        # Ограничение истории сообщений
        limit_msg = self._parameters.settings_model.history_messages_limit
        if len(self._messages) > limit_msg + 2:  # +1 системный
            self._messages = [self._messages[0]] + self._messages[-limit_msg:]

        return response_text

    def interrupt(self) -> None:
        """Прервать рассуждения модели"""
        self._interrupt_answer.set()

    def stop(self) -> None:
        """
        Остановка модели, высвобождение ресурсов памяти
        """
        if isinstance(self._model, Llama):
            self._model.close()
            self._model = None
            config.message_bus_add(
                level='stop',
                subcomponent='llm',
                message=f'Модель остановлена',
                event='stop model',
            )

    def interactive_chat(self) -> None:
        """Интерактивный чат для cli интерфейса"""
        while True:
            user_input = input('>>> ')
            if user_input == '':
                break
            # отправка запроса модели
            ask_thread = threading.Thread(
                target=self._ask_core,
                kwargs={'prompt': user_input, 'callback': lambda content: print(content, end="", flush=True), }
            )
            ask_thread.start()
            ask_thread.join()
            print()

    def ask(self, prompt: str) -> str:
        """
        Прямой запрос к llm, дожидается ответ от модели.
        Подходит для api, например ТГ бота или fastapi
        :param prompt: сообщение на которое модель собирается ответить
        :return : Возвращаемый моделью ответ
        """
        import queue
        result_queue = queue.Queue()
        threading.Thread(
            target=lambda: result_queue.put(self._ask_core(prompt=prompt))
        ).start()
        return result_queue.get()


if __name__ == '__main__':
    llm = Engine()
    llm.start(
        model_name='gemma-3-4b-it-GGUF',
        consent_to_upload=True,  # подтверждение что модели скачивать согласен
    )
    llm.interactive_chat()
    # print(llm.ask(prompt='Привет, меня зовут Mike. Как у тебя дела?'))
    # print(llm.ask(prompt='Спасибо, у меня тоже всё в порядке. У меня кстати чипсы, есть, много чипсов, будешь?'))
    # print(llm.ask(prompt='А ты помнишь как меня зовут, как я представился?'))

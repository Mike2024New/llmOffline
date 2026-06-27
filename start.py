import os
import sys
import subprocess
from pathlib import Path

"""
Стандарт : пусковой стартовый скрипт, для сборки зависимостей и скачивания необходимых компонентов.
"""

# удалить старый uv lock, так как он может помешать обновлению llama-cpp
uv_lock_path = Path('./uv.lock')
if uv_lock_path.exists():
    os.remove(uv_lock_path)

cmd = [sys.executable, '-m', 'pip', 'install', 'uv']
subprocess.run(cmd, shell=False)

# сборка версии 0.3.30 под cpu (потом можно будет параметризовать)
# на linux возможно придется установить доп утилиты: `sudo apt install build-essential cmake`
# для cpu (в будущем развитие до GPU, динамически выбирая radeon/geforce)
cmd = [
    sys.executable, '-m', 'uv', 'add', 'llama-cpp-python==0.3.30',
    '--extra-index-url', 'https://abetlen.github.io/llama-cpp-python/whl/cpu'
]
subprocess.run(cmd, shell=False)

# загрузка всех необходимых пакетов
cmd = [sys.executable, '-m', 'uv', 'sync']
subprocess.run(cmd, shell=False)

# принудительное обновление пакета infrasturcture (только с --upgrade-package)
subprocess.run(["uv", "lock", "--upgrade-package", "infrastructure"], check=True)
subprocess.run(["uv", "sync"], check=True)

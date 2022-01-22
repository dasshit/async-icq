# Импорт недавно установленного пакета setuptools.
import setuptools

import async_icq

with open("README.md", "r") as fh:
    long_description = fh.read()

# Определение requests как requirements для того, чтобы этот пакет работал.
# Зависимости проекта.
requirements = [
    "aiohttp>=3.8.1",
    "aiologger>=0.6.1",
    "aiosignal>=1.2.0",
    "async-timeout>=4.0.2",
    "attrs>=21.4.0",
    "charset-normalizer>=2.0.10",
    "frozenlist>=1.2.0",
    "idna>=3.3",
    "multidict>=5.2.0",
    "yarl>=1.7.2"
]

# Функция, которая принимает несколько аргументов.
# Она присваивает эти значения пакету.
setuptools.setup(
    # Имя дистрибутива пакета.
    # Оно должно быть уникальным,
    # поэтому добавление вашего имени пользователя
    # в конце является обычным делом.
    name="async_icq",
    # Номер версии вашего пакета.
    # Обычно используется семантическое управление версиями.
    version=async_icq.__version__,
    # Имя автора.
    author="Valerii Korobov",
    # Его почта.
    author_email="dasshit@yandex.ru",
    # Краткое описание, которое будет показано на странице PyPi.
    description="ICQ/VK Teams Bot API interface",
    # Длинное описание, которое будет отображаться на странице PyPi.
    # Использует README.md репозитория для заполнения.
    long_description=long_description,
    # Определяет тип контента, используемый в long_description.
    long_description_content_type="text/markdown",
    # URL-адрес, представляющий домашнюю страницу проекта.
    # Большинство проектов ссылаются на репозиторий.
    url="https://github.com/dasshit/async-icq",
    # Находит все пакеты внутри проекта и объединяет их в дистрибутив.
    packages=setuptools.find_packages(
        exclude=[
            "examples",
            ".github"
        ]
    ),
    # requirements или dependencies,
    # которые будут установлены вместе с пакетом,
    # когда пользователь установит его через pip.
    # install_requires=requirements,
    # предоставляет pip некоторые метаданные о пакете.
    # Также отображается на странице PyPi.
    install_requires=requirements,
    classifiers=[
        "Intended Audience :: Developers",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Topic :: Communications :: Chat",
        "Topic :: Internet",
        "Programming Language :: Python :: 3.5",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    keywords="mailru im bot api",
    # Требуемая версия Python.
    python_requires='>=3.5',
)

import os
import io
try:
    import ujson as json
except ImportError:
    import json
import asyncio

from types import MappingProxyType

from uuid import uuid4

import aiohttp

from aiohttp import ClientResponse

from aiologger import Logger
from aiologger.levels import LogLevel
from aiologger.formatters.base import Formatter

from typing import Optional, Dict, List, Union, Coroutine

from threading import Thread

from .events import Event, EventType
from .helpers import InlineKeyboardMarkup, Format

from .middleware import BaseBotMiddleware


def read_file(filepath: str) -> io.BytesIO:

    assert os.path.exists(filepath), f'File "{filepath}" does\'nt exist'
    assert os.path.isfile(filepath), f'"{filepath}" is not a file'

    with open(filepath, 'rb') as f:
        file_obj = io.BytesIO(f.read())
        file_obj.name = os.path.basename(filepath)
        return file_obj


async def async_read_file(filepath: str):
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(None, read_file, filepath)


def keyboard_to_json(
        keyboard_markup: Union[
            List[List[Dict]], InlineKeyboardMarkup, str, None
        ]
) -> Union[str, None]:
    if isinstance(keyboard_markup, InlineKeyboardMarkup):
        return keyboard_markup.to_json()
    elif isinstance(keyboard_markup, list):
        return json.dumps(keyboard_markup)
    elif isinstance(keyboard_markup, str):
        return keyboard_markup
    elif keyboard_markup is None:
        return keyboard_markup
    else:
        raise ValueError(
            f'Unsupported type: keyboard_markup ({type(keyboard_markup)})')


def format_to_json(format_: Union[Format, List[Dict], str]):
    if isinstance(format_, Format):
        return format_.to_json()
    elif isinstance(format_, list):
        return json.dumps(format_)
    elif isinstance(format_, str):
        return format_
    elif format_ is None:
        return format_
    else:
        raise ValueError(
            f'Unsupported type: format_ ({type(format_)})')


class AsyncBot(object):

    __slots__ = (
        "loop",
        "url",
        "session",
        "base_url",
        "parseMode",
        "token",
        "proxy",
        "logger",
        "running",
        "handlers",
        "help",
        "middlewares",
        "lastEventId",
        "pollTime",
        "__polling_thread"
    )

    def __init__(
            self,
            token: str,
            url: str = 'https://myteam.mail.ru',
            parseMode: str = 'HTML',
            proxy: Optional[str] = None,
            log_level: LogLevel = LogLevel.INFO,
            middlewares: List[BaseBotMiddleware] = (),
            lastEventId: int = 0,
            pollTime: int = 30,
            loop: Optional = None
    ):

        if loop is None:
            try:
                import uvloop
                asyncio.set_event_loop_policy(uvloop.EventLoopPolicy())
            except ImportError:
                pass
            self.loop = asyncio.new_event_loop()
        else:
            self.loop = loop

        self.session = None
        self.url: str = url
        self.base_url: str = f'{url}/bot/v1/'
        self.parseMode: str = parseMode
        self.token: str = token
        self.proxy: str = proxy

        self.logger = Logger.with_default_handlers(
            name='async-icq',
            formatter=Formatter(
                '%(name)s - '
                '%(levelname)s - '
                '%(module)s:%(funcName)s:%(lineno)d - '
                '%(message)s'
            ),
            level=log_level
        )

        self.running = True
        self.handlers: List = []
        self.help: List = []
        self.middlewares: List[BaseBotMiddleware] = middlewares

        self.lastEventId = lastEventId
        self.pollTime = pollTime

        self.__polling_thread: Optional[Thread] = None

        self.loop.run_until_complete(self.start_session())

        BaseBotMiddleware.bot = self
        Event.bot = self

        # gc.freeze()
        # gc.enable()

    @staticmethod
    def get_request_id() -> str:
        """
        Метод для создания уникального uuid запроса
        :return: уникальный uuid запроса
        """
        return str(uuid4())

    @staticmethod
    def loads(object) -> MappingProxyType:

        return MappingProxyType(
            json.loads(object)
        )

    async def start_session(self):
        """
        Функция создания асинхронной сессии
        :return: None
        """

        self.session: aiohttp.ClientSession = aiohttp.ClientSession(
            base_url=self.url,
            raise_for_status=True,
            timeout=aiohttp.ClientTimeout(total=self.pollTime + 5),
            json_serialize=json.dumps,
            loop=asyncio.get_event_loop()
        )

    async def get(self, path: str, **kwargs) -> ClientResponse:
        """
        Функция для создания и логирования GET-запроса
        :param path: относительный path запроса
        :param kwargs: параметры GET-запроса
        :return: ответ сервера
        """

        request_id = self.get_request_id()

        params = {
            'token': self.token
        }

        params.update(kwargs)

        for key, value in params.copy().items():

            if value is None:
                params.pop(key)

        await self.logger.debug(
            f'[GET][{request_id}] /bot/v1/{path} params - {kwargs} ->'
        )

        response = await self.session.get(
            url=f'/bot/v1/{path}',
            params=params,
            proxy=self.proxy
        )
        await self.logger.debug(
            f'[{response.status}] <- [{request_id}] /bot/v1/{path}'
        )
        return response

    async def post(
            self,
            path: str,
            data: Union[Dict[str, str], Dict[str, io.BytesIO]] = None,
            **kwargs
    ) -> ClientResponse:
        """
        Функция для создания и логирования POST-запроса
        :param path: относительный path запроса
        :param data:
        :param kwargs: параметры POST-запроса
        :return: ответ сервера
        """

        request_id = self.get_request_id()

        params = {
            'token': self.token
        }

        params.update(kwargs)

        for key, value in params.copy().items():

            if value is None:
                params.pop(key)

        self.logger.debug(
            f'[POST][{request_id}] {path} kwargs - {kwargs} ->'
        )

        response = await self.session.post(
                url=f'/bot/v1/{path}',
                params=params,
                data=data,
                proxy=self.proxy
        )
        self.logger.debug(
            f'<- [{response.status}][{request_id}]'
        )
        return response

    async def self_get(self,) -> ClientResponse:
        """
        Метод можно использовать для проверки валидности токена.
        :return: Сервер вернул информацию о боте. Пример:

        {
            "userId": "747432131",
            "nick": "test_api_bot",
            "firstName": "TestBot",
            "about": "The description of the bot",
            "photo": [{
                "url": "https://example.com/image.png"
            }],
            "ok": true
        }
        """
        return await self.get('self/get')

    async def send_text(
            self,
            chatId: str,
            text: str,
            replyMsgId: Optional[List[str]] = None,
            forwardChatId: Optional[str] = None,
            forwardMsgId: Optional[List[str]] = None,
            inlineKeyboardMarkup: Union[
                List[List[Dict[str, str]]], InlineKeyboardMarkup, None] = None,
            _format: Union[Format, List[Dict], str, None] = None,
            parseMode: Optional[str] = None
    ) -> ClientResponse:
        """
        Метод для отправки текстового сообщения
        :param chatId: Уникальный ник или id чата или пользователя.
        Id можно получить из входящих events (поле chatId).
        :param text: Текст сообщения. Можно упомянуть пользователя,
        добавив в текст его userId в следующем формате @[userId].
        :param replyMsgId: Id цитируемого сообщения.
        Не может быть передано одновременно
        с параметрами forwardChatId и forwardMsgId.
        :param forwardChatId: Id чата, из которого будет переслано сообщение.
        Передается только с forwardMsgId.
        Не может быть передано с параметром replyMsgId.
        :param forwardMsgId: Id пересылаемого сообщения.
        Передается только с forwardChatId.
        Не может быть передано с параметром replyMsgId.
        :param inlineKeyboardMarkup: Это массив массивов с описанием кнопок.
        Верхний уровень это массив строк кнопок,
        ниже уровнем массив кнопок в конкретной строке
        :param _format: Описание форматирования текста.
        :param parseMode: Режим обработки форматирования из текста сообщения.
        :return: Результат отправки сообщения. Пример:

        {
            "msgId": "57883346846815032",
            "ok": true
        }
        """
        return await self.get(
            path='messages/sendText',
            chatId=chatId,
            text=text,
            replyMsgId=replyMsgId,
            forwardChatId=forwardChatId,
            forwardMsgId=forwardMsgId,
            inlineKeyboardMarkup=inlineKeyboardMarkup
            if isinstance(inlineKeyboardMarkup, str)
            else keyboard_to_json(inlineKeyboardMarkup),
            format=_format
            if isinstance(_format, str)
            else format_to_json(_format),
            parseMode=parseMode if parseMode is not None else self.parseMode
        )

    async def send_fileId(
            self,
            chatId: str,
            fileId: str,
            caption: Optional[str] = None,
            replyMsgId: Optional[List[int]] = None,
            forwardChatId: Optional[str] = None,
            forwardMsgId: Optional[List[int]] = None,
            inlineKeyboardMarkup: Union[
                List[List[Dict[str, str]]], InlineKeyboardMarkup, None] = None,
            _format: Union[Format, List[Dict], str, None] = None,
            parseMode: Optional[str] = None
    ) -> ClientResponse:
        """
        Метод для отправки сообщения
        с уже ранее загруженным файлом по его fileId.
        :param chatId: Уникальный ник или id чата или пользователя.
        Id можно получить из входящих events (поле chatId).
        :param fileId: Id ранее загруженного файла.
        :param caption: Подпись к файлу.
        :param replyMsgId: Id цитируемого сообщения.
        Не может быть передано одновременно
        с параметрами forwardChatId и forwardMsgId.
        :param forwardChatId: Id чата, из которого будет переслано сообщение.
        Передается только с forwardMsgId.
        Не может быть передано с параметром replyMsgId.
        :param forwardMsgId: Id пересылаемого сообщения.
        Передается только с forwardChatId.
        Не может быть передано с параметром replyMsgId.
        :param inlineKeyboardMarkup: Это массив массивов с описанием кнопок.
        Верхний уровень это массив строк кнопок,
        ниже уровнем массив кнопок в конкретной строке
        :param _format: Описание форматирования текста.
        :param parseMode: Режим обработки форматирования из текста сообщения.
        :return: Результат отправки сообщения. Пример:

        {
            "msgId": "57883346846815032",
            "ok": true
        }
        """
        return await self.get(
            path='messages/sendFile',
            chatId=chatId,
            fileId=fileId,
            caption=caption,
            replyMsgId=replyMsgId,
            forwardChatId=forwardChatId,
            forwardMsgId=forwardMsgId,
            inlineKeyboardMarkup=inlineKeyboardMarkup
            if isinstance(inlineKeyboardMarkup, str)
            else keyboard_to_json(inlineKeyboardMarkup),
            format=_format
            if isinstance(_format, str)
            else format_to_json(_format),
            parseMode=parseMode if parseMode is not None else self.parseMode
        )

    async def send_file(
        self,
        chatId: str,
        file_path: str,
        caption: Optional[str] = None,
        replyMsgId: Optional[List[int]] = None,
        forwardChatId: Optional[str] = None,
        forwardMsgId: Optional[List[int]] = None,
        inlineKeyboardMarkup: Union[
                List[List[Dict[str, str]]], InlineKeyboardMarkup, None] = None,
        _format: Union[Format, List[Dict], str, None] = None,
        parseMode: Optional[str] = None
    ) -> ClientResponse:
        """
        Метод для отправки сообщения с файлом по его file.
        """
        return await self.post(
            path='messages/sendFile',
            chatId=chatId,
            data={'file': await async_read_file(file_path)},
            caption=caption,
            replyMsgId=replyMsgId,
            forwardChatId=forwardChatId,
            forwardMsgId=forwardMsgId,
            inlineKeyboardMarkup=inlineKeyboardMarkup
            if isinstance(inlineKeyboardMarkup, str)
            else keyboard_to_json(inlineKeyboardMarkup),
            format=_format
            if isinstance(_format, str)
            else format_to_json(_format),
            parseMode=parseMode
            if parseMode is not None
            else self.parseMode
        )

    async def send_voiceId(
            self,
            chatId: str,
            fileId: str,
            replyMsgId: Optional[List[int]] = None,
            forwardChatId: Optional[str] = None,
            forwardMsgId: Optional[List[int]] = None,
            inlineKeyboardMarkup: Union[
                List[List[Dict[str, str]]], InlineKeyboardMarkup, None] = None,
    ) -> ClientResponse:
        """
        Метод отправки предзагруженного голосового сообщения по его id
        :param chatId: Уникальный ник или id чата или пользователя.
        Id можно получить из входящих events (поле chatId).
        :param fileId: Id ранее загруженного файла.
        :param replyMsgId: Id цитируемого сообщения.
        Не может быть передано одновременно
        с параметрами forwardChatId и forwardMsgId.
        :param forwardChatId: Id чата, из которого будет переслано сообщение.
        Передается только с forwardMsgId.
        Не может быть передано с параметром replyMsgId.
        :param forwardMsgId: Id пересылаемого сообщения.
        Передается только с forwardChatId.
        Не может быть передано с параметром replyMsgId.
        :param inlineKeyboardMarkup: Это массив массивов с описанием кнопок.
        Верхний уровень это массив строк кнопок,
        ниже уровнем массив кнопок в конкретной строке
        :return: Сервер вернул id сообщения. Пример:

        {
            "msgId": "57883346846815032",
            "ok": true
        }
        """
        return await self.get(
            path='messages/sendVoice',
            chatId=chatId,
            fileId=fileId,
            replyMsgId=replyMsgId,
            forwardChatId=forwardChatId,
            forwardMsgId=forwardMsgId,
            inlineKeyboardMarkup=inlineKeyboardMarkup
            if isinstance(inlineKeyboardMarkup, str)
            else keyboard_to_json(inlineKeyboardMarkup),
        )

    async def send_voice(
        self,
        chatId: str,
        file_path: str,
        caption: Optional[str] = None,
        replyMsgId: Optional[List[int]] = None,
        forwardChatId: Optional[str] = None,
        forwardMsgId: Optional[List[int]] = None,
        inlineKeyboardMarkup: Union[
                List[List[Dict[str, str]]], InlineKeyboardMarkup, None] = None,
        _format: Union[Format, List[Dict], str, None] = None,
        parseMode: Optional[str] = None
    ) -> ClientResponse:
        """
        Метод для отправки сообщения с голосового сообщения по его file,
        он должен быть в формате aac, ogg или m4a.
        """
        return await self.post(
            path='messages/sendVoice',
            chatId=chatId,
            data={'file': await async_read_file(file_path)},
            caption=caption,
            replyMsgId=replyMsgId,
            forwardChatId=forwardChatId,
            forwardMsgId=forwardMsgId,
            inlineKeyboardMarkup=inlineKeyboardMarkup
            if isinstance(inlineKeyboardMarkup, str)
            else keyboard_to_json(inlineKeyboardMarkup),
            format=_format
            if isinstance(_format, str)
            else format_to_json(_format),
            parseMode=parseMode
            if parseMode is not None
            else self.parseMode
        )

    async def edit_text(
            self,
            chatId: str,
            msgId: int,
            text: str,
            inlineKeyboardMarkup: Union[
                List[List[Dict[str, str]]], InlineKeyboardMarkup, None] = None,
            _format: Union[Format, List[Dict], str, None] = None,
            parseMode: Optional[str] = None
    ) -> ClientResponse:
        """
        Метод редактирования уже отправленного сообщения
        :param chatId: Уникальный ник или id чата или пользователя.
        Id можно получить из входящих events (поле chatId).
        :param msgId: Id сообщения.
        :param text: Текст сообщения.
        Можно упомянуть пользователя,
        добавив в текст его userId в следующем формате @[userId].
        :param inlineKeyboardMarkup: Это массив массивов с описанием кнопок.
        Верхний уровень это массив строк кнопок,
        ниже уровнем массив кнопок в конкретной строке
        :param _format: Описание форматирования текста.
        :param parseMode: Режим обработки форматирования из текста сообщения.
        :return: Результат обработки запроса. Пример:

        {
            "ok": true
        }
        """
        return await self.get(
            path='messages/editText',
            chatId=chatId,
            msgId=msgId,
            text=text,
            inlineKeyboardMarkup=inlineKeyboardMarkup
            if isinstance(inlineKeyboardMarkup, str)
            else keyboard_to_json(inlineKeyboardMarkup),
            format=_format
            if isinstance(_format, str)
            else format_to_json(_format),
            parseMode=parseMode if parseMode is not None else self.parseMode
        )

    async def delete_msg(
            self,
            chatId: str,
            msgId: List[str]
    ) -> ClientResponse:
        """
        Метод удаления списка уже отправленных сообщений

        На удаление наложены следующие ограничения:
            Сообщение может быть удалено только если оно было отправлено
            менее 48 часов назад;
            Бот может удалить исходящие сообщения в приватных чатах и группах;
            Бот может удалить любое сообщение в группе,
            если он является администратором.
        :param chatId: Уникальный ник или id чата или пользователя.
        Id можно получить из входящих events (поле chatId).
        :param msgId: Id сообщений
        :return: Результат обработки запроса. Пример:

        {
            "ok": true
        }
        """
        return await self.get(
            path="messages/deleteMessages",
            chatId=chatId,
            msgId=msgId
        )

    async def answer_callback_query(
            self,
            queryId: str,
            text: Optional[str] = None,
            showAlert: bool = False,
            url: Optional[str] = None
    ) -> ClientResponse:
        """
        Вызов данного метода должен использоваться
        в ответ на получение события [callbackQuery]
        :param queryId: Идентификатор callback query полученного ботом
        :param text: Текст нотификации, который будет отображен пользователю.
        В случае, если текст не задан – ничего не будет отображено.
        :param showAlert: Если выставить значение в true,
        вместо нотификации будет показан alert
        :param url: URL, который будет открыт клиентским приложением
        :return: Результат обработки запроса. Пример:

        {
            "ok": true
        }
        """
        return await self.get(
            path='messages/answerCallbackQuery',
            queryId=queryId,
            text=text,
            showAlert='true' if showAlert else 'false',
            url=url
        )

    async def create_chat(
            self,
            name: str,
            about: Optional[str] = None,
            rules: Optional[str] = None,
            members: Optional[List[str]] = None,
            public: Optional[str] = "true",
            defaultRole: Optional[str] = "member",
            joinModeration: Optional[str] = "true"
    ) -> ClientResponse:
        """
        Создать чат или канал.

        Этот метод доступен только в специальных сборках on-premise/myteam.
        Если вы хотите его использовать, попросите вашего
        системного администратора добавить /chats/createChat <botId>
        в таблицу bot_api_private_methods.
        :param name: Название чата.
        :param about: Описание чата.
        :param rules: Правила чата.
        :param members: Список пользователей
        :param public: Публичность чата
        :param defaultRole: Роль по умолчанию
        ('member' для групп, 'readonly' для каналов)
        :param joinModeration: Требуется ли подтверждение вступления.
        :return:Результат обработки запроса. Пример:

        {
            "sn": "681869378@chat.agent"
        }
        """
        return await self.get(
            path="chats/createChat",
            name=name,
            about=about,
            rules=rules,
            members=[{"sn": member} for member in members],
            public=public,
            defaultRole=defaultRole,
            joinModeration=joinModeration
        )

    async def add_members(
            self,
            chatId: str,
            members: List[str]
    ) -> ClientResponse:
        """
        Добавить пользователей в чат.

        Этот метод доступен только в специальных сборках on-premise/myteam.
        Если вы хотите его использовать, попросите
        вашего системного администратора добавить /chats/members/add <botId>
        в таблицу bot_api_private_methods.
        :param chatId: Уникальный ник или id группы или канала.
        Id можно получить из входящих events (поле chatId).
        :param members: Список пользователей
        :return: Результат обработки запроса. Пример:

        {
            "ok": true
        }
        """
        return await self.get(
            path="chats/members/add",
            chatId=chatId,
            members=[{"sn": member} for member in members],
        )

    async def delete_members(
            self,
            chatId: str,
            members: List[str]
    ) -> ClientResponse:
        """
        Метод удаления пользователей из чата
        :param chatId: Уникальный ник или id группы или канала.
        Id можно получить из входящих events (поле chatId).
        :param members: Список пользователей
        :return: Результат обработки запроса. Пример:

        {
            "ok": true
        }
        """
        return await self.get(
            path="chats/members/delete",
            chatId=chatId,
            members=[{"sn": member} for member in members],
        )

    async def send_actions(
            self,
            chatId: str,
            actions: str
    ) -> ClientResponse:
        """
        Необходимо вызывать этот метод каждый раз
        при изменении текущих действий, или каждые 10 секунд,
        если действия не изменились. После отправки запроса
        без активных действий повторно уведомлять об их отсутствии не следует.
        :param chatId: Уникальный ник или id чата или пользователя.
        Id можно получить из входящих events (поле chatId).
        :param actions: Текущие действия в чате.
        Отправьте пустое значение, если все действия завершены.
        Available values : looking, typing
        :return: Результат обработки запроса. Пример:

        {
            "ok": true
        }
        """
        return await self.get(
            path="chats/sendActions",
            chatId=chatId,
            actions=actions,
        )

    async def get_chat_info(
            self,
            chatId: str,
    ) -> ClientResponse:
        """
        Метод получение информации о чате
        :param chatId: Уникальный ник или id чата или пользователя.
        Id можно получить из входящих events (поле chatId).
        :return: Результат обработки запроса. Пример:

        {
            "type": "group",
            "title": "TestGroup",
            "about": "Group description",
            "rules": "Group rules",
            "inviteLink": "https://example.com/chat/AoLFkoRCn4MpaP0DjUI",
            "public": true,
            "joinModeration": true
        }
        """
        return await self.get(
            path="chats/getInfo",
            chatId=chatId,
        )

    async def get_chat_admins(
            self,
            chatId: str,
    ) -> ClientResponse:
        """
        Метод получения списка администраторов чата
        :param chatId: Уникальный ник или id группы или канала.
        Id можно получить из входящих events (поле chatId).
        :return: Сервер вернул список админов в чате. Пример:

        {
            "admins": [
                {
                    "userId": "string",
                    "creator": true
                }
            ]
        }
        """
        return await self.get(
            path="chats/getAdmins",
            chatId=chatId,
        )

    async def get_chat_members(
            self,
            chatId: str,
            cursor: Optional[str] = None
    ) -> ClientResponse:
        """
        Метод для получения списка пользователей чата
        :param chatId: ID чата
        :param cursor: курсор, используется если количество пользователей более
         определенного лимита
        :return: Список пользователей чата
        """
        return await self.get(
            path="chats/getAdmins",
            chatId=chatId,
            cursor=cursor
        )

    async def get_chat_blocked_users(
            self,
            chatId: str,
    ) -> ClientResponse:
        """
        Метод для получения списка заблокированных пользователей в чате
        :param chatId: ID чата
        :return: Список заблокированных пользователей
        """
        return await self.get(
            path="chats/getBlockedUsers",
            chatId=chatId,
        )

    async def get_chat_pending_users(
            self,
            chatId: str,
    ) -> ClientResponse:
        """
        Метод для получения списка пользователей, желающих вступить в чат
        :param chatId: ID чата
        :return: список пользователей
        """
        return await self.get(
            path="chats/getPendingUsers",
            chatId=chatId,
        )

    async def block_user(
            self,
            chatId: str,
            userId: str,
            delLastMessages: bool = True
    ) -> ClientResponse:
        """
        Метод для блокировки пользователей в чате
        :param chatId: ID чата
        :param userId: ID пользователя
        :param delLastMessages: удалять ли сообщения пользователя
        :return: результат запроса
        """
        return await self.get(
            path="chats/blockUser",
            chatId=chatId,
            userId=userId,
            delLastMessages=delLastMessages
        )

    async def unblock_user(
            self,
            chatId: str,
            userId: str,
    ) -> ClientResponse:
        """
        Метод для разблокировки пользователя в чате
        :param chatId: ID чата
        :param userId: ID пользователя
        :return: результат запроса
        """
        return await self.get(
            path="chats/unblockUser",
            chatId=chatId,
            userId=userId,
        )

    async def resolvePending(
            self,
            chatId: str,
            approve: bool = True,
            userId: Optional[str] = None,
            everyone: bool = True
    ) -> ClientResponse:
        """
        Метод для одобрения вступления пользователя в чат
        :param chatId: ID чата
        :param approve: разрешить или запретить в вступление
        :param userId: ID пользователя
        :param everyone: Флаг для разрешения вступления всех пользователей что
        хотят в чат вступить
        :return: результат запроса
        """
        if everyone:
            return await self.get(
                path="chats/resolvePending",
                chatId=chatId,
                approve=approve,
                everyone=everyone
            )
        else:
            return await self.get(
                path="chats/resolvePending",
                chatId=chatId,
                approve=approve,
                userId=userId,
                everyone=everyone
            )

    async def set_chat_title(
            self,
            chatId: str,
            title: str
    ) -> ClientResponse:
        """
        Метод для установки названия чата
        :param chatId: ID чата
        :param title: новое название
        :return: результат запроса
        """
        return await self.get(
            path="chats/setTitle",
            chatId=chatId,
            title=title,
        )

    async def set_chat_about(
            self,
            chatId: str,
            about: str
    ) -> ClientResponse:
        """
        Метод для установки описания чата
        :param chatId: ID чата
        :param about: новое описание чата
        :return: результат запроса
        """
        return await self.get(
            path="chats/setAbout",
            chatId=chatId,
            about=about,
        )

    async def set_chat_rules(
            self,
            chatId: str,
            rules: str
    ) -> ClientResponse:
        """
        Метод для установки новых правил чата
        :param chatId: ID чата
        :param rules: новые правила чата
        :return: результат запроса
        """
        return await self.get(
            path="chats/setRules",
            chatId=chatId,
            rules=rules,
        )

    async def pin_msg(
            self,
            chatId: str,
            msgId: str
    ) -> ClientResponse:
        """
        Метод для закрепления сообщения в чате
        :param chatId: ID чата
        :param msgId: ID сообщения
        :return: результат запроса
        """
        return await self.get(
            path="chats/pinMessage",
            chatId=chatId,
            msgId=msgId,
        )

    async def unpin_msg(
            self,
            chatId: str,
            msgId: str
    ) -> ClientResponse:
        """
        Метод для закрепления сообщения в чате
        :param chatId: ID чата
        :param msgId: ID сообщения
        :return: результат запроса
        """
        return await self.get(
            path="chats/unpinMessage",
            chatId=chatId,
            msgId=msgId,
        )

    async def get_file_info(
            self,
            fileId: str
    ) -> ClientResponse:
        """
        Получение информации о файле по его fileId
        :param fileId: ID файла
        :return: информация о файле
        """
        return await self.get(
            path="files/getInfo",
            fileId=fileId
        )

    @staticmethod
    def loads(object, *args, **kwargs) -> MappingProxyType:
        return MappingProxyType(
            json.loads(object)
        )

    async def get_events(self):
        """
        Метод для поллинга событий от Bit API
        :return: Список событий
        """
        response = await self.get(
            path="events/get",
            lastEventId=self.lastEventId,
            pollTime=self.pollTime
        )

        response_json = await response.json(
            loads=self.loads
        )

        if response_json.get('events', []):

            self.lastEventId = response_json['events'][-1]['eventId']

        return response_json['events']

    async def handle_wrapper(self, handler, event: Event):

        try:
            await handler(event)
        except Exception as error:
            await self.logger.exception(error)

    async def sync_handle_wrapper(self, handler, event: Event):

        try:
            handler(self, event)
        except Exception as error:
            await self.logger.exception(error)

    async def middleware_check(self, event_: Event):
        for middleware in self.middlewares:
            if event_.type in middleware.event_types:
                if asyncio.iscoroutinefunction(middleware.check):
                    result = await middleware.check(event_)
                    if result:
                        return True
                elif middleware.check(event_):
                    return True
        return False

    def task_check(self, event_, handler, event_type, cmd) -> Optional[Coroutine]:

        try:
            if (event_type == event_.type and cmd is None) \
                    or \
                    (event_type == EventType.NEW_MESSAGE == event_.type \
                     and event_.text.startswith(cmd)):
                return self.handle_wrapper(
                    handler=handler,
                    event=event_
                )
        except Exception:
            pass

    async def process_event(self, event: Event):

        await self.logger.debug(event)

        if await self.middleware_check(event):
            yield

        if event.text is not None:
            if event.text == '/help':
                yield self.handle_wrapper(
                    handler=self.help_info,
                    event=event
                )
                return

        for part in filter(
                    lambda x: x is not None,
                    map(
                        lambda x: self.task_check(
                            event, *x,
                        ),
                        self.handlers
                    )
                ):

           yield part

    async def start_polling(self):
        """
        Функция поллинга и обработки событий
        :return:
        """
        while self.running:

            try:

                await asyncio.wait([
                    proccessed_event for event_ in map(
                        lambda event: Event(
                            type_=EventType(event["type"]),
                            data=event["payload"]
                        ),
                        await self.get_events()
                    ) async for proccessed_event in self.process_event(event_)
                ])

            except ValueError:
                continue

            except KeyboardInterrupt as error:
                await self.logger.info(f'Stopping bot after {type(error)}')
                break

            except Exception as error:
                await self.logger.exception(error)

    async def help_info(self, event: Event):

        text = "Возможные команды:\n\n" + '\n'.join([
            f"<pre>{cmd} - {info}</pre>" for cmd, info in self.help
        ])

        await event.answer(text)

    def start_poll(self, threaded: bool = False):
        """
        Перегрузка функции поллинга и обрабоки событий
        :param threaded: выполнять функцию в основном потоке

        или запустить побочный
        :return:
        """

        self.add_handler([self.help_info, EventType.NEW_MESSAGE, '/help'])

        if threaded:

            self.__polling_thread = Thread(
                target=self.loop.run_until_complete,
                args=[self.start_polling()],
                daemon=True
            )
            self.__polling_thread.start()

        else:

            self.loop.run_until_complete(self.start_polling())

    def add_handler(self, handler: List):
        """
        Функция добавления обработчика событий
        :param handler:
        :return:
        """
        if asyncio.iscoroutinefunction(handler[0]):
            self.handlers.append(handler)
            if handler[0].__doc__:
                if handler[1] == EventType.NEW_MESSAGE:
                    self.help.append([
                        "Любое сообщение" if handler[2] is None else handler[2],
                        handler[0].__doc__.strip()
                    ])
                elif handler[1] == EventType.EDITED_MESSAGE:
                    self.help.append([
                        "Редактирование любого сообщения",
                        handler[0].__doc__.strip()
                    ])
                elif handler[1] == EventType.DELETED_MESSAGE:
                    self.help.append([
                        "Удаление сообщения в чате",
                        handler[0].__doc__.strip()
                    ])
                elif handler[1] == EventType.CALLBACK_QUERY:
                    self.help.append([
                        "Нажатие на ботокнопку",
                        handler[0].__doc__.strip()
                    ])
                elif handler[1] == EventType.PINNED_MESSAGE:
                    self.help.append([
                        "Закрепление сообщения в чате",
                        handler[0].__doc__.strip()
                    ])
                elif handler[1] == EventType.UNPINNED_MESSAGE:
                    self.help.append([
                        "Открепление сообщения в чате",
                        handler[0].__doc__.strip()
                    ])
                elif handler[1] == EventType.NEW_CHAT_MEMBERS:
                    self.help.append([
                        "Добавление нового участника в чат",
                        handler[0].__doc__.strip()
                    ])
                elif handler[1] == EventType.LEFT_CHAT_MEMBERS:
                    self.help.append([
                        "Удаление участника в чат",
                        handler[0].__doc__.strip()
                    ])
                elif handler[1] == EventType.CHANGED_CHAT_INFO:
                    self.help.append([
                        "Изменение информации о чате",
                        handler[0].__doc__.strip()
                    ])
        else:
            raise ValueError(
                f'Added unsupported sync event handler: {handler[0].__name__}'
            )

    def event_handler(self, event_type: EventType, cmd: Optional[str] = None):
        """
        Базовый декоратор для функции обработки события
        :param event_type: ALL
        :param cmd: ?
        :return:
        """
        def decorate(handler):
            self.add_handler([handler, event_type, cmd])
            return handler
        return decorate

    def message_handler(self, event_type: EventType = EventType.NEW_MESSAGE):
        """
        Декоратор для функций обработки входящих сообщений
        :param event_type: тип события = EventType.NEW_MESSAGE
        :return:
        """
        def decorate(handler):
            self.add_handler([handler, event_type, None])
            return handler
        return decorate

    def command_handler(
            self,
            cmd: str,
            event_type: EventType = EventType.NEW_MESSAGE
    ):
        """
        Декоратор для функций обработки входящих сообщений
        :param event_type: тип события = EventType.NEW_MESSAGE
        :param cmd:
        :return:
        """
        def decorate(handler):
            self.add_handler([handler, event_type, cmd])
            return handler
        return decorate

    def start_handler(
            self,
            cmd: str = '/start',
            event_type: EventType = EventType.NEW_MESSAGE
    ):
        """
        Декоратор для функций обработки входящих сообщений
        :param event_type: тип события = EventType.NEW_MESSAGE
        :param cmd:
        :return:
        """
        def decorate(handler):
            self.add_handler([handler, event_type, cmd])
            return handler
        return decorate

    def edit_handler(
            self,
            event_type: EventType = EventType.EDITED_MESSAGE,
            cmd: Optional[str] = None
    ):
        """
        Декоратор для функции обработки события редактирования сообщения
        :param event_type: тип события = EventType.EDIT_MESSAGE
        :param cmd: -
        :return:
        """
        def decorate(handler):
            self.add_handler([handler, event_type, cmd])
            return handler
        return decorate

    def delete_handler(
            self,
            event_type: EventType = EventType.DELETED_MESSAGE,
            cmd: Optional[str] = None
    ):
        """
        Декоратор для функции обработки события удаления сообщения
        :param event_type: тип события = EventType.DELETE_MESSAGE
        :param cmd: -
        :return:
        """
        def decorate(handler):
            self.add_handler([handler, event_type, cmd])
            return handler
        return decorate

    def pin_handler(
            self,
            event_type: EventType = EventType.PINNED_MESSAGE,
            cmd: Optional[str] = None
    ):
        """
        Декоратор для функции обработки события закрепления сообщения в чате
        :param event_type: тип события = EventType.PIN_MESSAGE
        :param cmd: -
        :return:
        """
        def decorate(handler):
            self.add_handler([handler, event_type, cmd])
            return handler
        return decorate

    def unpin_handler(
            self,
            event_type: EventType = EventType.UNPINNED_MESSAGE,
            cmd: Optional[str] = None
    ):
        """
        Декоратор для функции обработки события открепления сообщения в чате
        :param event_type: тип события = EventType.UNPIN_MESSAGE
        :param cmd: -
        :return:
        """
        def decorate(handler):
            self.add_handler([handler, event_type, cmd])
            return handler
        return decorate

    def new_member_handler(
            self,
            event_type: EventType = EventType.NEW_CHAT_MEMBERS,
            cmd: Optional[str] = None
    ):
        """
        Декоратор для фукнции обработки
        события добавления нового пользователя в чат
        :param event_type: тип события = EventType.NEW_CHAT_MEMBERS
        :param cmd: -
        :return:
        """
        def decorate(handler):
            self.add_handler([handler, event_type, cmd])
            return handler
        return decorate

    def left_chat_handler(
            self,
            event_type: EventType = EventType.LEFT_CHAT_MEMBERS,
            cmd: Optional[str] = None
    ):
        """
        Декоратор для функции обработки события удаления пользователя из чата
        :param event_type: тип события = EventType.LEFT_CHAT_MEMBERS
        :param cmd: -
        :return:
        """
        def decorate(handler):
            self.add_handler([handler, event_type, cmd])
            return handler
        return decorate

    def changed_chat_info_handler(
            self,
            event_type: EventType = EventType.CHANGED_CHAT_INFO,
            cmd: Optional[str] = None
    ):
        """
        Декоратор для функции обработки события обновления информации о чате
        :param event_type: тип события = EventType.CHANGED_CHAT_INFO
        :param cmd: -
        :return:
        """
        def decorate(handler):
            self.add_handler([handler, event_type, cmd])
            return handler
        return decorate

    def callback(
            self,
            event_type: EventType = EventType.CALLBACK_QUERY,
            cmd: Optional[str] = None
    ):
        """
        Декоратор для функции обработки события клика по кнопке с коллбеком
        :param event_type: тип события = EventType.CALLBACK_QUERY
        :param cmd: -
        :return:
        """
        def decorate(handler):
            self.add_handler([handler, event_type, cmd])
            return handler
        return decorate

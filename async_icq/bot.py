import json
import asyncio

import aiohttp

from aiohttp import ClientResponse

from aiologger import Logger
from aiologger.levels import LogLevel
from aiologger.formatters.base import Formatter

from typing import Optional, Dict, List, Union

from threading import Thread

from .events import Event, EventType
from .helpers import InlineKeyboardMarkup, Format

from .middleware import BaseBotMiddleware


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

    def __init__(
            self,
            token: str,
            url: str = 'https://myteam.mail.ru',
            parseMode: str = 'HTML',
            proxy: Optional[str] = None,
            middlewares: List[BaseBotMiddleware] = [],
            lastEventId: int = 0,
            pollTime: int = 30
    ):

        self.loop = asyncio.new_event_loop()

        self.session = None
        self.url: str = url
        self.base_url: str = f'{url}/bot/v1/'
        self.parseMode: str = parseMode
        self.token: str = token
        self.proxy: str = proxy

        self.logger = Logger.with_default_handlers(
            name='async-icq',
            formatter=Formatter(
                '%(asctime)s - '
                '%(name)s - '
                '%(levelname)s - '
                '%(module)s:%(funcName)s:%(lineno)d - '
                '%(message)s'
            ),
            level=LogLevel.INFO
        )

        self.running = True
        self.handlers: List = []
        self.middlewares: List[BaseBotMiddleware] = middlewares

        self.lastEventId = lastEventId
        self.pollTime = pollTime

        self.__polling_thread: Optional[Thread] = None

        self.loop.run_until_complete(self.start_session())

        BaseBotMiddleware.bot = self

    async def start_session(self):
        """
        Функция создания асинхронной сессии
        :return: None
        """
        self.session: aiohttp.ClientSession = aiohttp.ClientSession(
            base_url=self.url,
            raise_for_status=True,
            timeout=aiohttp.ClientTimeout(total=self.pollTime)
        )

    async def get(self, path: str, **kwargs) -> ClientResponse:
        """
        Функция для создания и логирования GET-запроса
        :param path: относительный path запроса
        :param kwargs: параметры GET-запроса
        :return: ответ сервера
        """
        params = {
            'token': self.token
        }

        params.update(kwargs)

        for key, value in params.copy().items():

            if value is None:
                params.pop(key)

        await self.logger.debug(
            f'[GET] /bot/v1/{path} params - {kwargs} ->'
        )

        response = await self.session.get(
            url=f'/bot/v1/{path}',
            params=params,
            proxy=self.proxy
        )
        await self.logger.debug(
            f'<- [{response.status}] /bot/v1/{path}'
        )
        return response

    async def post(self, path: str, **kwargs) -> ClientResponse:
        """
        Функция для создания и логирования POST-запроса
        :param path: относительный path запроса
        :param kwargs: параметры POST-запроса
        :return: ответ сервера
        """
        params = {
            'token': self.token
        }

        params.update(kwargs)

        self.logger.debug(
            f'[POST] {path} kwargs - {kwargs} ->'
        )

        async with self.session.post(
                url=f'{self.base_url}{path}',
                params=params,
                proxy=self.proxy
        ) as response:
            self.logger.debug(
                f'<- [{response.status}]'
            )
            return await response.json()

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
            replyMsgId: Optional[List[int]] = None,
            forwardChatId: Optional[str] = None,
            forwardMsgId: Optional[List[int]] = None,
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

        return await self.get(
            path="chats/getAdmins",
            chatId=chatId,
            cursor=cursor
        )

    async def get_chat_blocked_users(
            self,
            chatId: str,
    ) -> ClientResponse:

        return await self.get(
            path="chats/getBlockedUsers",
            chatId=chatId,
        )

    async def get_chat_pending_users(
            self,
            chatId: str,
    ) -> ClientResponse:

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

        return await self.get(
            path="chats/setRules",
            chatId=chatId,
            rules=rules,
        )

    async def pin_msg(
            self,
            chatId: str,
            msgId: int
    ) -> ClientResponse:

        return await self.get(
            path="chats/pinMessage",
            chatId=chatId,
            msgId=msgId,
        )

    async def get_file_info(
            self,
            fileId: str
    ) -> ClientResponse:

        return await self.get(
            path="files/getInfo",
            fileId=fileId
        )

    async def get_events(self):

        response = await self.get(
            path="events/get",
            lastEventId=self.lastEventId,
            pollTime=self.pollTime
        )

        response_json = await response.json()

        if response_json.get('events', []):

            self.lastEventId = response_json['events'][-1]['eventId']

        return response_json

    async def handle_wrapper(self, handler, event: Event):

        try:
            await handler(self, event)
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
                else:
                    if middleware.check(event_):
                        return True
        return False

    async def start_polling(self):

        while self.running:

            try:
                events = await self.get_events()

                events = [
                    Event(
                        type_=EventType(event["type"]),
                        data=event["payload"]
                    )
                    for event in events['events']
                ]

                tasks = []

                for event_ in events:
                    await self.logger.debug(event_)

                    middleware_check = await self.middleware_check(event_)
                    if middleware_check:
                        continue

                    for handler, event_type, cmd in self.handlers:
                        if event_type == event_.type and cmd is None:
                            tasks.append(
                                self.handle_wrapper(
                                    handler=handler,
                                    event=event_
                                )
                            )
                        elif cmd is not None \
                                and event_type == EventType.NEW_MESSAGE \
                                and event_type == event_.type \
                                and event_.text.startswith(cmd):
                            tasks.append(
                                self.handle_wrapper(
                                    handler=handler,
                                    event=event_
                                )
                            )
                        else:
                            await self.logger.debug(
                                f'Passing event: {event_.type} {event_.data}'
                            )

                if tasks:
                    await asyncio.wait(tasks, timeout=0)
            except (
                    asyncio.exceptions.TimeoutError,
                    aiohttp.client_exceptions.ServerTimeoutError
            ) as error:
                await self.logger.error(error)

    def start_poll(self, threaded: bool = False):

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

        if asyncio.iscoroutinefunction(handler[0]):
            self.handlers.append(handler)
        else:
            raise ValueError(
                f'Added unsupported sync event handler: {handler[0].__name__}'
            )

    def event_handler(self, event_type: EventType, cmd: Optional[str] = None):

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

        def decorate(handler):
            self.add_handler([handler, event_type, cmd])
            return handler
        return decorate

    def delete_handler(
            self,
            event_type: EventType = EventType.DELETED_MESSAGE,
            cmd: Optional[str] = None
    ):

        def decorate(handler):
            self.add_handler([handler, event_type, cmd])
            return handler
        return decorate

    def pin_handler(
            self,
            event_type: EventType = EventType.PINNED_MESSAGE,
            cmd: Optional[str] = None
    ):

        def decorate(handler):
            self.add_handler([handler, event_type, cmd])
            return handler
        return decorate

    def unpin_handler(
            self,
            event_type: EventType = EventType.UNPINNED_MESSAGE,
            cmd: Optional[str] = None
    ):

        def decorate(handler):
            self.add_handler([handler, event_type, cmd])
            return handler
        return decorate

    def new_member_handler(
            self,
            event_type: EventType = EventType.NEW_CHAT_MEMBERS,
            cmd: Optional[str] = None
    ):

        def decorate(handler):
            self.add_handler([handler, event_type, cmd])
            return handler
        return decorate

    def left_chat_handler(
            self,
            event_type: EventType = EventType.LEFT_CHAT_MEMBERS,
            cmd: Optional[str] = None
    ):

        def decorate(handler):
            self.add_handler([handler, event_type, cmd])
            return handler
        return decorate

    def changed_chat_info_handler(
            self,
            event_type: EventType = EventType.CHANGED_CHAT_INFO,
            cmd: Optional[str] = None
    ):

        def decorate(handler):
            self.add_handler([handler, event_type, cmd])
            return handler
        return decorate

    def callback(
            self,
            event_type: EventType = EventType.CALLBACK_QUERY,
            cmd: Optional[str] = None
    ):

        def decorate(handler):
            self.add_handler([handler, event_type, cmd])
            return handler
        return decorate

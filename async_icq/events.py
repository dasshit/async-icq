from enum import Enum, unique

from aiohttp import ClientResponse

from typing import Dict, List, Optional, Union

# from .bot import AsyncBot
from .helpers import InlineKeyboardMarkup, Format


@unique
class EventType(Enum):
    NEW_MESSAGE = "newMessage"
    EDITED_MESSAGE = "editedMessage"
    DELETED_MESSAGE = "deletedMessage"
    PINNED_MESSAGE = "pinnedMessage"
    UNPINNED_MESSAGE = "unpinnedMessage"
    NEW_CHAT_MEMBERS = "newChatMembers"
    LEFT_CHAT_MEMBERS = "leftChatMembers"
    CHANGED_CHAT_INFO = "changedChatInfo"
    CALLBACK_QUERY = "callbackQuery"


class ChatInfo(object):
    def __init__(self, chatId: str, type: str, title: Optional[str] = None):
        self.chatId: str = chatId
        self.type: str = type
        self.title = title

    def __repr__(self):
        return "{self.title}({self.chatId})".format(
            self=self)


class UserInfo(object):
    def __init__(
            self,
            userId: str,
            firstName: Optional[str] = None,
            lastName: Optional[str] = None,
            nick: Optional[str] = None
    ):
        self.userId: str = userId
        self.firstName: str = firstName
        self.lastName: str = lastName
        self.nick: str = nick

    def __repr__(self):
        return "{self.firstName} {self.lastName}({self.userId})".format(
            self=self)


class Event(object):

    bot = None

    def __init__(self, type_, data):
        super(Event, self).__init__()

        self.type = type_
        self.data = data

        if type_ != EventType.CALLBACK_QUERY:
            self.chat: ChatInfo = ChatInfo(**data['chat'])

        if type_ in [
            EventType.NEW_MESSAGE,
            EventType.EDITED_MESSAGE,
            EventType.PINNED_MESSAGE
        ]:
            self.from_: UserInfo = UserInfo(**data['from'])
            self.text: str = data.get('text')
            self._format: Dict[str, List[Dict[str, int]]] = data.get('format')
            self.timestamp: int = data.get('timestamp')
            self.msgId: str = data.get('msgId')
        elif type_ in [
            EventType.DELETED_MESSAGE,
            EventType.UNPINNED_MESSAGE
        ]:
            self.timestamp: int = data.get('timestamp')
            self.msgId: str = data.get('msgId')
        elif type_ in [
            EventType.NEW_CHAT_MEMBERS,
            EventType.LEFT_CHAT_MEMBERS
        ]:
            self.newMembers = [
                UserInfo(**user) for user in data.get('newMembers', [])
            ]
            if data.get('addedBy'):
                self.addedBy = UserInfo(**data['addedBy'])
        else:
            self.queryId = data['queryId']
            self.from_ = UserInfo(**data['from'])
            self.cb_message = Event(
                EventType.NEW_MESSAGE,
                data['message']
            )
            self.callbackData = data['callbackData']

    def __repr__(self):
        return "Event(type='{self.type}', data='{self.data}')".format(
            self=self)

    async def answer(
            self,
            text: str,
            inlineKeyboardMarkup: Union[
                List[List[Dict[str, str]]], InlineKeyboardMarkup, None] = None,
            _format: Union[Format, List[Dict], str, None] = None,
            parseMode: Optional[str] = None
    ) -> ClientResponse:
        """
        Простой ответ на входящее сообщение в тот же чат
        :param text: текст ответа
        :param inlineKeyboardMarkup: кнопки к ответному сообщению
        :param _format: форматирование сообщения
        :param parseMode: метод форматирования
        :return: результат запроса на ответ
        """
        return await self.bot.send_text(
            chatId=self.chat.chatId,
            text=text,
            inlineKeyboardMarkup=inlineKeyboardMarkup,
            _format=_format,
            parseMode=parseMode
        )

    async def reply_msg(
            self,
            text: str,
            inlineKeyboardMarkup: Union[
                List[List[Dict[str, str]]], InlineKeyboardMarkup, None] = None,
            _format: Union[Format, List[Dict], str, None] = None,
            parseMode: Optional[str] = None
    ) -> ClientResponse:
        """
        Ответ на сообщение в виде реплая
        :param text: текст ответа
        :param inlineKeyboardMarkup: кнопки к ответу
        :param _format: форматирование текста ответа
        :param parseMode: метод форматирования текста в ответе
        :return: результат запроса
        """
        return await self.bot.send_text(
            chatId=self.chat.chatId,
            text=text,
            replyMsgId=[self.msgId],
            inlineKeyboardMarkup=inlineKeyboardMarkup,
            _format=_format,
            parseMode=parseMode
        )

    async def forward_msg(
            self,
            text: str,
            forwardChatId: Optional[str] = None,
            inlineKeyboardMarkup: Union[
                List[List[Dict[str, str]]], InlineKeyboardMarkup, None] = None,
            _format: Union[Format, List[Dict], str, None] = None,
            parseMode: Optional[str] = None
    ) -> ClientResponse:
        """
        Пересылка входящего сообщения в указанный чат
        :param text: комментарий к пересланному сообщению
        :param forwardChatId: ID чата, куда нужно сообщение переслать
        :param inlineKeyboardMarkup: кнопки к пересылаемому сообщению
        :param _format: форматирование комментария
        :param parseMode: метод форматирования
        :return: результат запроса
        """
        return await self.bot.send_text(
            chatId=forwardChatId,
            text=text,
            forwardChatId=self.chat.chatId,
            forwardMsgId=[self.msgId],
            inlineKeyboardMarkup=inlineKeyboardMarkup,
            _format=_format,
            parseMode=parseMode
        )

    async def answer_by_fileId(
            self,
            fileId: str,
            caption: Optional[str] = None,
            replyMsgId: Optional[List[int]] = None,
            forwardChatId: Optional[str] = None,
            forwardMsgId: Optional[List[int]] = None,
            inlineKeyboardMarkup: Union[
                List[List[Dict[str, str]]], InlineKeyboardMarkup, None] = None,
            _format: Union[Format, List[Dict], str, None] = None,
            parseMode: Optional[str] = None
    ):
        """
        Отправить в ответ на событие файл по его ID
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
        return await self.bot.send_fileId(
            chatId=self.chat.chatId,
            fileId=fileId,
            caption=caption,
            replyMsgId=replyMsgId,
            forwardChatId=forwardChatId,
            forwardMsgId=forwardMsgId,
            inlineKeyboardMarkup=inlineKeyboardMarkup,
            _format=_format,
            parseMode=parseMode
        )

    async def answer_by_file(
            self,
            file_path: str,
            caption: Optional[str] = None,
            replyMsgId: Optional[List[int]] = None,
            forwardChatId: Optional[str] = None,
            forwardMsgId: Optional[List[int]] = None,
            inlineKeyboardMarkup: Union[
                List[List[Dict[str, str]]], InlineKeyboardMarkup, None] = None,
            _format: Union[Format, List[Dict], str, None] = None,
            parseMode: Optional[str] = None
    ):
        """
        Отправить в ответ на событие файл по его ID
        :param file_path: Путь к файлу
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
        return await self.bot.send_file(
            chatId=self.chat.chatId,
            file_path=file_path,
            caption=caption,
            replyMsgId=replyMsgId,
            forwardChatId=forwardChatId,
            forwardMsgId=forwardMsgId,
            inlineKeyboardMarkup=inlineKeyboardMarkup,
            _format=_format,
            parseMode=parseMode
        )

    async def answer_by_voiceId(
            self,
            fileId: str,
            caption: Optional[str] = None,
            replyMsgId: Optional[List[int]] = None,
            forwardChatId: Optional[str] = None,
            forwardMsgId: Optional[List[int]] = None,
            inlineKeyboardMarkup: Union[
                List[List[Dict[str, str]]], InlineKeyboardMarkup, None] = None,
            _format: Union[Format, List[Dict], str, None] = None,
            parseMode: Optional[str] = None
    ):
        """
        Метод отправки предзагруженного голосового сообщения по его id
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
        return await self.bot.send_fileId(
            chatId=self.chat.chatId,
            fileId=fileId,
            caption=caption,
            replyMsgId=replyMsgId,
            forwardChatId=forwardChatId,
            forwardMsgId=forwardMsgId,
            inlineKeyboardMarkup=inlineKeyboardMarkup,
            _format=_format,
            parseMode=parseMode
        )

    async def answer_by_voice(
            self,
            file_path: str,
            caption: Optional[str] = None,
            replyMsgId: Optional[List[int]] = None,
            forwardChatId: Optional[str] = None,
            forwardMsgId: Optional[List[int]] = None,
            inlineKeyboardMarkup: Union[
                List[List[Dict[str, str]]], InlineKeyboardMarkup, None] = None,
            _format: Union[Format, List[Dict], str, None] = None,
            parseMode: Optional[str] = None
    ):
        """
        Метод отправки предзагруженного голосового сообщения по его id
        :param file_path: Путь к файлу
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
        return await self.bot.send_voice(
            chatId=self.chat.chatId,
            file_path=file_path,
            caption=caption,
            replyMsgId=replyMsgId,
            forwardChatId=forwardChatId,
            forwardMsgId=forwardMsgId,
            inlineKeyboardMarkup=inlineKeyboardMarkup,
            _format=_format,
            parseMode=parseMode
        )

    async def delete_msg(self) -> ClientResponse:
        """
        Удалить входящее сообщение
        :return: результат запроса
        """
        return await self.bot.delete_msg(
            chatId=self.chat.chatId,
            msgId=[self.msgId]
        )

    async def pin_msg(self) -> ClientResponse:
        """
        Закрепить входящее сообщение в чате
        :return: результат запроса
        """
        return await self.bot.pin_msg(
            chatId=self.chat.chatId,
            msgId=self.msgId
        )

    async def unpin_msg(self) -> ClientResponse:
        """
        Открепить входящее сообщение в чате
        :return: результат запроса
        """
        return await self.bot.unpin_msg(
            chatId=self.chat.chatId,
            msgId=self.msgId
        )

    async def set_title_msg_text(self) -> ClientResponse:
        """
        Установка текста входящего сообщения в качестве названия чата
        :return: результат запроса
        """
        return await self.bot.set_chat_title(
            chatId=self.chat.chatId,
            title=self.text
        )

    async def set_about_msg_text(self) -> ClientResponse:
        """
        Установка текста входящего сообщения в качестве описания чата
        :return: результат запроса
        """
        return await self.bot.set_chat_about(
            chatId=self.chat.chatId,
            about=self.text
        )

    async def set_rules_msg_text(self) -> ClientResponse:
        """
        Установка текста входящего сообщения в качестве правил чата
        :return: результат запроса
        """
        return await self.bot.set_chat_rules(
            chatId=self.chat.chatId,
            rules=self.text
        )

    async def answer_callback(
            self,
            text: Optional[str] = None,
            showAlert: bool = False,
            url: Optional[str] = None
    ) -> ClientResponse:
        """
        Вызов данного метода должен использоваться
        в ответ на получение события [callbackQuery]
        :param text: Текст нотификации, который будет отображен пользователю.
        В случае, если текст не задан – ничего не будет отображено.
        :param showAlert: Если выставить значение в true,
        вместо нотификации будет показан alert
        :param url: URL, который будет открыт клиентским приложением
        :return: результат запроса
        """
        return await self.bot.answer_callback_query(
            queryId=self.queryId,
            text=text,
            showAlert=showAlert,
            url=url
        )

    async def block_member(
            self,
            delLastMessages: bool = True
    ) -> ClientResponse:
        """
        Блокировка автора события в чате
        :param delLastMessages: Удалить ли сообщения пользователя в чате
        :return: результат запроса
        """
        return await self.bot.block_user(
            chatId=self.chat.chatId,
            userId=self.from_.userId,
            delLastMessages=delLastMessages
        )

    async def delete_member(self) -> ClientResponse:
        """
        Удаление автора события
        :return: результат запроса
        """
        return await self.bot.delete_members(
            chatId=self.chat.chatId,
            members=[self.from_.userId]
        )

    async def log(self, msg: Optional[str] = None):
        """
        Вывести msg в лог
        """
        if msg is None:
            await self.bot.logger.info(f'event - {self.data}')
        else:
            await self.bot.logger.info(msg)

import asyncio
import aiohttp

from aiologger import Logger

from typing import Optional, Dict, List

from threading import Thread

from events import Event, EventType


async def logging_func(bot, event: Event):

    await asyncio.sleep(2)

    await bot.logger.info(event)

    await asyncio.sleep(2)


class AsyncBot(object):

    def __init__(
            self,
            token: str,
            url: str = 'https://myteam.mail.ru',
            parseMode: str = 'HTML',
            proxy: Optional[str] = None,
            lastEventId: int = 0,
            pollTime: int = 10
    ):

        self.loop = asyncio.new_event_loop()

        self.session = None
        self.url: str = url
        self.base_url: str = f'{url}/bot/v1/'
        self.parseMode: str = parseMode
        self.token: str = token
        self.proxy: str = proxy

        self.logger = Logger.with_default_handlers(name='async-icq')

        self.running = True
        self.handlers: List = []

        self.lastEventId = lastEventId
        self.pollTime = pollTime

        self.__polling_thread: Optional[Thread] = None

        self.loop.run_until_complete(self.start_session())

    async def start_session(self):
        self.session: aiohttp.ClientSession = aiohttp.ClientSession(
            base_url=self.url,
            raise_for_status=True,
            read_timeout=40,
            conn_timeout=4,

        )

    async def get(self, path: str, **kwargs) -> Dict:

        params = {
            'token': self.token
        }

        params.update(kwargs)

        for key, value in params.copy().items():

            if value is None:
                params.pop(key)

        await self.logger.debug(
            f'[GET] {path} kwargs - {kwargs} ->'
        )

        async with self.session.get(
            url=f'/bot/v1/{path}',
            params=params,
            proxy=self.proxy
        ) as response:
            await self.logger.debug(
                f'<- [{response.status}]'
            )
            return await response.json()

    async def post(self, path: str, **kwargs) -> Dict:

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

    async def self_get(self,) -> Dict:

        return await self.get('self/get')

    async def send_text(
            self,
            chatId: str,
            text: str,
            replyMsgId: Optional[List[int]] = None,
            forwardChatId: Optional[str] = None,
            forwardMsgId: Optional[List[int]] = None,
            inlineKeyboardMarkup: Optional[List[List[Dict[str, str]]]] = None,
            _format: Optional[Dict[str, str]] = None,
            parseMode: Optional[str] = None
    ) -> Dict:

        return await self.get(
            path='messages/sendText',
            chatId=chatId,
            text=text,
            replyMsgId=replyMsgId,
            forwardChatId=forwardChatId,
            forwardMsgId=forwardMsgId,
            inlineKeyboardMarkup=inlineKeyboardMarkup,
            format=_format,
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
            inlineKeyboardMarkup: Optional[List[List[Dict[str, str]]]] = None,
            _format: Optional[Dict[str, str]] = None,
            parseMode: Optional[str] = None
    ) -> Dict:

        return await self.get(
            path='messages/sendFile',
            chatId=chatId,
            fileId=fileId,
            caption=caption,
            replyMsgId=replyMsgId,
            forwardChatId=forwardChatId,
            forwardMsgId=forwardMsgId,
            inlineKeyboardMarkup=inlineKeyboardMarkup,
            format=_format,
            parseMode=parseMode if parseMode is not None else self.parseMode
        )

    async def send_voiceId(
            self,
            chatId: str,
            fileId: str,
            caption: Optional[str] = None,
            replyMsgId: Optional[List[int]] = None,
            forwardChatId: Optional[str] = None,
            forwardMsgId: Optional[List[int]] = None,
            inlineKeyboardMarkup: Optional[List[List[Dict[str, str]]]] = None,
            _format: Optional[Dict[str, str]] = None,
            parseMode: Optional[str] = None
    ) -> Dict:

        return await self.get(
            path='messages/sendVoice',
            chatId=chatId,
            fileId=fileId,
            caption=caption,
            replyMsgId=replyMsgId,
            forwardChatId=forwardChatId,
            forwardMsgId=forwardMsgId,
            inlineKeyboardMarkup=inlineKeyboardMarkup,
            format=_format,
            parseMode=parseMode if parseMode is not None else self.parseMode
        )

    async def edit_text(
            self,
            chatId: str,
            msgId: int,
            text: str,
            inlineKeyboardMarkup: Optional[List[List[Dict[str, str]]]] = None,
            _format: Optional[Dict[str, str]] = None,
            parseMode: Optional[str] = None
    ) -> Dict:

        return await self.get(
            path='messages/editText',
            chatId=chatId,
            msgId=msgId,
            text=text,
            inlineKeyboardMarkup=inlineKeyboardMarkup,
            format=_format,
            parseMode=parseMode if parseMode is not None else self.parseMode
        )

    async def delete_msg(
            self,
            chatId: str,
            msgId: List[str]
    ) -> Dict:

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
    ) -> Dict:

        return await self.get(
            path='messages/answerCallbackQuery',
            queryId=queryId,
            text=text,
            showAlert=showAlert,
            url=url
        )

    async def create_chat(
            self,
            name: str,
            about: Optional[str] = None,
            rules: Optional[str] = None,
            members: Optional[List[Dict[str, str]]] = None,
            public: Optional[str] = "true",
            defaultRole: Optional[str] = "member",
            joinModeration: Optional[str] = "true"
    ) -> Dict:

        return await self.get(
            path="chats/createChat",
            name=name,
            about=about,
            rules=rules,
            members=members,
            public=public,
            defaultRole=defaultRole,
            joinModeration=joinModeration
        )

    async def add_members(
            self,
            chatId: str,
            members: List[Dict[str, str]]
    ) -> Dict:

        return await self.get(
            path="chats/members/add",
            chatId=chatId,
            members=members,
        )

    async def delete_members(
            self,
            chatId: str,
            members: List[Dict[str, str]]
    ) -> Dict:

        return await self.get(
            path="chats/members/delete",
            chatId=chatId,
            members=members,
        )

    async def send_actions(
            self,
            chatId: str,
            actions: List[str]
    ) -> Dict:

        return await self.get(
            path="chats/sendActions",
            chatId=chatId,
            actions=actions,
        )

    async def get_chat_info(
            self,
            chatId: str,
    ) -> Dict:

        return await self.get(
            path="chats/getInfo",
            chatId=chatId,
        )

    async def get_chat_admins(
            self,
            chatId: str,
    ) -> Dict:

        return await self.get(
            path="chats/getAdmins",
            chatId=chatId,
        )

    async def get_chat_members(
            self,
            chatId: str,
            cursor: Optional[str] = None
    ) -> Dict:

        return await self.get(
            path="chats/getAdmins",
            chatId=chatId,
            cursor=cursor
        )

    async def get_chat_blocked_users(
            self,
            chatId: str,
    ) -> Dict:

        return await self.get(
            path="chats/getBlockedUsers",
            chatId=chatId,
        )

    async def get_chat_pending_users(
            self,
            chatId: str,
    ) -> Dict:

        return await self.get(
            path="chats/getPendingUsers",
            chatId=chatId,
        )

    async def block_user(
            self,
            chatId: str,
            userId: str,
            delLastMessages: bool = True
    ) -> Dict:

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
    ) -> Dict:

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
    ) -> Dict:

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
    ) -> Dict:

        return await self.get(
            path="chats/setTitle",
            chatId=chatId,
            title=title,
        )

    async def set_chat_about(
            self,
            chatId: str,
            about: str
    ) -> Dict:

        return await self.get(
            path="chats/setAbout",
            chatId=chatId,
            about=about,
        )

    async def set_chat_rules(
            self,
            chatId: str,
            rules: str
    ) -> Dict:

        return await self.get(
            path="chats/setRules",
            chatId=chatId,
            rules=rules,
        )

    async def pin_msg(
            self,
            chatId: str,
            msgId: int
    ) -> Dict:

        return await self.get(
            path="chats/pinMessage",
            chatId=chatId,
            msgId=msgId,
        )

    async def get_file_info(
            self,
            fileId: str
    ) -> Dict:

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

        if response.get('events', []):

            self.lastEventId = response['events'][-1]['eventId']

        return response

    async def start_polling(self):

        while self.running:

            events = await self.get_events()

            events = [
                Event(
                    type_=EventType(event["type"]),
                    data=event["payload"]
                )
                for event in events['events']
            ]

            tasks = [
                handler(
                    self,
                    event_
                )
                for event_ in events
                for handler, event_type in self.handlers if event_type == event_.type
            ]

            if tasks:
                await asyncio.wait(tasks, timeout=0)

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

        self.handlers.append(handler)

    def event_handler(self, event_type):

        def decorate(handler):
            self.add_handler([handler, event_type])
            return handler
        return decorate

    def message_handler(self, event_type: EventType = EventType.NEW_MESSAGE):

        def decorate(handler):
            self.add_handler([handler, event_type])
            return handler
        return decorate

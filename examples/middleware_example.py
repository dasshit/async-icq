from async_icq.events import EventType, Event

from async_icq.middleware import BaseBotMiddleware


class AuthMiddleWare(BaseBotMiddleware):

    def __init__(self, chat_id: str, password: str, *args):
        self.chat_id = chat_id
        self.pwd = password
        self.list = set(args)
        self.event_types = {
            EventType.NEW_MESSAGE
        }

    async def check(self, event: Event) -> bool:

        await AuthMiddleWare.bot.logger.debug(f'Checking event: {event.data}')

        if event.chat.chatId != self.chat_id:
            return False

        if event.from_.userId not in self.list:

            if event.text == self.pwd:

                self.list.add(event.from_.userId)

                return False

            await AuthMiddleWare.bot.delete_msg(
                chatId=event.chat.chatId,
                msgId=[event.msgId]
            )

            text = 'We are not suppose to talk, auth_list: \n'

            text += '\n'.join([f'@[{user}]' for user in self.list])

            await AuthMiddleWare.bot.send_text(
                chatId=event.from_.userId,
                text=text
            )

            text = f'User @[{event.from_.userId}] ' \
                   f'isn\'t allowed to talk in this chat'

            await AuthMiddleWare.bot.send_text(
                chatId=event.chat.chatId,
                text=text
            )

            return True
        else:
            return False

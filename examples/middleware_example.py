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

        if event.from_chat != self.chat_id:
            return False

        if event.message_author['userId'] not in self.list:

            if event.text == self.pwd:

                self.list.add(event.message_author['userId'])

                return False

            await AuthMiddleWare.bot.delete_msg(
                chatId=event.from_chat,
                msgId=[event.msgId]
            )

            text = 'We are not suppose to talk, auth_list: \n'

            text += '\n'.join([f'@[{user}]' for user in self.list])

            await AuthMiddleWare.bot.send_text(
                chatId=event.message_author['userId'],
                text=text
            )

            text = f'User @[{event.message_author["userId"]}] ' \
                   f'isn\'t allowed to talk in this chat'

            await AuthMiddleWare.bot.send_text(
                chatId=event.from_chat,
                text=text
            )

            return True
        else:
            return False

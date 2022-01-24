import asyncio

import random

from async_icq.bot import AsyncBot
from async_icq.events import Event
from async_icq.helpers import InlineKeyboardMarkup, KeyboardButton

from aiologger.levels import LogLevel

from middleware_example import AuthMiddleWare


testbot = AsyncBot(
    token='001.2002552977.3511691778:1000002608',
    url='https://api.internal.myteam.mail.ru',
    middlewares=[
        AuthMiddleWare(
            '1@chat.agent',
            '4231',
            'test.user.1@corp.mail.ru',
        )
    ],
    log_level=LogLevel.DEBUG
)


@testbot.message_handler()
async def hello(event: Event):

    try:
        timer = random.randint(5, 10)

        await event.log(
            f'Starting await {timer} seconds after msg "{event.text}"')

        await asyncio.sleep(timer)

        markup = InlineKeyboardMarkup()

        markup.row(
            KeyboardButton(
                text='Button callbackdata',
                callbackData='test|data'
            )
        )

        markup.row(
            KeyboardButton(
                text='Button url',
                url='https://mail.ru/'
            )
        )

        await event.bot.send_text(
            chatId=event.chat.chatId,
            text=f'Test {timer} secs',
            inlineKeyboardMarkup=markup
        )

        await event.answer(
            text=f'Test {timer} secs',
            inlineKeyboardMarkup=markup
        )

        await event.reply_msg(
            text=f'Test {timer} secs',
            inlineKeyboardMarkup=markup
        )

        await event.forward_msg(
            text=f'Test {timer} secs',
            forwardChatId=event.chat.chatId,
            inlineKeyboardMarkup=markup
        )

        await event.log(
            f'Ending await {timer} seconds after msg "{event.text}"')
    except Exception as error:
        await event.bot.logger.exception(error)


@testbot.callback()
async def callback(event: Event):

    await event.log(f'Callback {event.data}')

    await event.answer_callback(
        text=f'{event.callbackData}|{event.from_.userId}'
    )


testbot.start_poll()

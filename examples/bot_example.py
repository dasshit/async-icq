import asyncio

import random

from async_icq.bot_class import AsyncBot
from async_icq.events import Event
from async_icq.helpers import InlineKeyboardMarkup, KeyboardButton

from middleware_example import AuthMiddleWare


testbot = AsyncBot(
    token='TOKEN',
    url='https://api.internal.myteam.mail.ru',
    middlewares=[
        AuthMiddleWare(
            '1@chat.agent',
            '4231',
            'test.user.1@corp.mail.ru',
        )
    ],
)


@testbot.message_handler()
async def hello(bot: AsyncBot, event: Event):

    try:
        timer = random.randint(5, 10)

        await bot.logger.debug(
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

        await bot.send_text(
            chatId=event.from_chat,
            text=f'Test {timer} secs',
            inlineKeyboardMarkup=markup
        )

        await bot.logger.debug(
            f'Ending await {timer} seconds after msg "{event.text}"')
    except Exception as error:
        await bot.logger.exception(error)


@testbot.callback()
async def callback(bot: AsyncBot, event: Event):

    await bot.logger.debug(f'Callback {event.data}')

    await bot.answer_callback_query(
        queryId=event.queryId,
        text=event.callback_query
    )


testbot.start_poll()

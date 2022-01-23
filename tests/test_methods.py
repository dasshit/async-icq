import os
import pytest
from async_icq.bot import AsyncBot
from async_icq.helpers import InlineKeyboardMarkup, KeyboardButton


prepare_bot = AsyncBot(
        token=os.getenv('TOKEN'),
        url=os.getenv('API_URL'),
)

ADMIN_CHAT_ID = os.getenv('ADMIN_CHAT_ID')


@pytest.mark.asyncio
async def test_send_text():

    await prepare_bot.start_session()

    response = await prepare_bot.send_text(
        chatId=ADMIN_CHAT_ID,
        text=f'Hi, @[{ADMIN_CHAT_ID}]'
    )

    resp_json = await response.json()

    assert resp_json.get('msgId')
    assert resp_json.get('ok')


@pytest.mark.asyncio
async def test_send_text_with_keyboard():

    await prepare_bot.start_session()

    markup = InlineKeyboardMarkup()

    markup.row(
        KeyboardButton(
            text='Button URL',
            url='https://mail.ru/'
        )
    )

    markup.row(
        KeyboardButton(
            text='Button callback',
            callbackData='button|callback'
        )
    )

    response = await prepare_bot.send_text(
        chatId=ADMIN_CHAT_ID,
        text=f'Hi, @[{ADMIN_CHAT_ID}]',
        inlineKeyboardMarkup=markup
    )

    resp_json = await response.json()

    assert resp_json.get('msgId')
    assert resp_json.get('ok')

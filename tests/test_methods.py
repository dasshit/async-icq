import os
import pytest
import pytest_asyncio
from async_icq.bot import AsyncBot
from async_icq.helpers import InlineKeyboardMarkup, KeyboardButton


ADMIN_CHAT_ID = os.getenv('ADMIN_CHAT_ID')

bot = AsyncBot(
    token=os.getenv('TOKEN'),
    url=os.getenv('API_URL'),
)


@pytest_asyncio.fixture
async def prepare_bot():

    await bot.start_session()

    yield bot


@pytest.mark.asyncio
@pytest.mark.parametrize(
    'text', [
        f'Hi, @[{ADMIN_CHAT_ID}]',
        f'```Test, @[{ADMIN_CHAT_ID}]```',
        '<code>def test():\n    pass</code>'
    ],
    ids=[
        'mention',
        'backtiks with mention',
        'HTML-formatting'
    ]
)
async def test_send_text(
        prepare_bot,
        text
):

    response = await prepare_bot.send_text(
        chatId=ADMIN_CHAT_ID,
        text=f'Hi, @[{ADMIN_CHAT_ID}]'
    )

    resp_json = await response.json()

    assert resp_json.get('msgId')
    assert resp_json.get('ok')


@pytest.mark.asyncio
@pytest.mark.parametrize(
    'text', [
        f'Hi, @[{ADMIN_CHAT_ID}]',
        f'```Test, @[{ADMIN_CHAT_ID}]```',
        '<code>def test():\n    pass</code>'
    ],
    ids=[
        'mention',
        'backtiks with mention',
        'HTML-formatting'
    ]
)
async def test_send_text_with_keyboard(
        prepare_bot,
        text
):

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

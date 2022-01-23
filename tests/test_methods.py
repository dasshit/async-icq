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
        '<code>def test():\n    pass</code>',
        f'<i>Test @[{ADMIN_CHAT_ID}]</i>'
    ],
    ids=[
        'mention',
        'backtiks with mention',
        'HTML-code',
        'HTML-italic'
    ]
)
@pytest.mark.parametrize(
    'keyboard', [
        True,
        False
    ],
    ids=[
        'with keyboard',
        'none keyboard'
    ]
)
async def test_send_text(
        prepare_bot: AsyncBot,
        text: str,
        keyboard: bool
):
    if keyboard:
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
    else:
        markup = None

    response = await prepare_bot.send_text(
        chatId=ADMIN_CHAT_ID,
        text=f'Hi, @[{ADMIN_CHAT_ID}]',
        inlineKeyboardMarkup=markup
    )

    resp_json = await response.json()

    assert resp_json.get('msgId')
    assert resp_json.get('ok')

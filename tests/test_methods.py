import os
import pytest
import pytest_asyncio
from typing import Optional
from async_icq.bot import AsyncBot
from async_icq.helpers import InlineKeyboardMarkup, KeyboardButton


ADMIN_CHAT_ID = os.getenv('ADMIN_CHAT_ID')

bot = AsyncBot(
    token=os.getenv('TOKEN'),
    url=os.getenv('API_URL'),
)

msg_id: Optional[str] = None


@pytest_asyncio.fixture
async def prepare_bot():

    await bot.start_session()

    yield bot


@pytest_asyncio.fixture
async def prepare_msg(
        prepare_bot: AsyncBot
):
    global msg_id

    if msg_id is None:
        response = await prepare_bot.send_text(
            chatId=ADMIN_CHAT_ID,
            text='Forward Test'
        )

        resp_json = await response.json()

        msg_id = resp_json.get('msgId')

    yield msg_id


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
@pytest.mark.parametrize(
    'fwd_or_reply', [
        None,
        'forward',
        'reply'
    ],
    ids=[
        'nothing',
        'with forward',
        'with reply'
    ]
)
async def test_send_text(
        prepare_bot: AsyncBot,
        prepare_msg: Optional[str],
        text: str,
        keyboard: bool,
        fwd_or_reply: str
):
    replyMsgId = None
    forwardChatId = None
    forwardMsgId = None

    if fwd_or_reply == 'forward':

        forwardChatId = ADMIN_CHAT_ID

        forwardMsgId = [
            prepare_msg
        ]

    elif fwd_or_reply == 'reply':

        replyMsgId = [
            prepare_msg
        ]
    else:
        forwardChatId = None

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
        forwardMsgId=forwardMsgId,
        forwardChatId=forwardChatId,
        replyMsgId=replyMsgId,
        inlineKeyboardMarkup=markup
    )

    resp_json = await response.json()

    assert resp_json.get('msgId')
    assert resp_json.get('ok')


@pytest.mark.asyncio
@pytest.mark.parametrize(
    'fileId', [
        "02B6g000g9Fpjf1eRmkxju61eaec281bb",
        "Q8Iq8cgZQIiiprKnuD86vk61eaed711bb",
        "zfhqNk6SKLwc0KYLPgTBPX61eaf0641bb",
        "y7ltdslLWscY1yiogtwFpx61eaee9e1bb",
        "I0006XIfaT937afKh78ISw61eabec41bb",
        "W51lurUgrOo8WjnGFJUPgs61e968121bb"
    ],
    ids=[
        "image",
        "ics",
        "pdf",
        "txt",
        "ptt",
        "log"
    ]
)
@pytest.mark.parametrize(
    "caption", [
        None,
        "test",
        "<code>test</code>",
        "```test```"
    ],
    ids=[
        'without caption',
        'basic caption',
        'html-formatted caption',
        'backtick-formatted caption'
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
@pytest.mark.parametrize(
    'fwd_or_reply', [
        None,
        'forward',
        'reply'
    ],
    ids=[
        'nothing',
        'with forward',
        'with reply'
    ]
)
async def test_send_fileId(
        prepare_bot: AsyncBot,
        prepare_msg: Optional[str],
        fileId: str,
        caption: Optional[str],
        keyboard: bool,
        fwd_or_reply: str
):
    replyMsgId = None
    forwardChatId = None
    forwardMsgId = None

    if fwd_or_reply == 'forward':

        forwardChatId = ADMIN_CHAT_ID

        forwardMsgId = [
            prepare_msg
        ]

    elif fwd_or_reply == 'reply':

        replyMsgId = [
            prepare_msg
        ]
    else:
        forwardChatId = None

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

    response = await prepare_bot.send_fileId(
        chatId=ADMIN_CHAT_ID,
        fileId=fileId,
        forwardMsgId=forwardMsgId,
        forwardChatId=forwardChatId,
        replyMsgId=replyMsgId,
        inlineKeyboardMarkup=markup
    )

    resp_json = await response.json()

    assert resp_json.get('msgId')
    assert resp_json.get('ok')




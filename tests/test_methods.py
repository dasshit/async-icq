import os

print(os.environ)

import pytest

from async_icq.bot_class import AsyncBot


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

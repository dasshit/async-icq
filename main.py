from bot import AsyncBot
from events import Event, EventType


testbot = AsyncBot(
    token='TOKEN',
    url='https://api.icq.net',
)


@testbot.event_handler(EventType.EDITED_MESSAGE)
@testbot.message_handler()
async def hello(bot: AsyncBot, event: Event):
    response = await bot.send_text(
        chatId='test',
        text="qwerbqwreb".join([str(i) for i in range(1000)])
    )

    await bot.logger.debug(response)

testbot.start_poll()

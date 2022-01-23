# Async ICQ/VK Teams bot API wrapper

<img src="https://github.com/mail-ru-im/bot-python/blob/master/logo.png" width="100" height="100">

Pure Async Python interface for Bot API.

# Table of contents
- [Introduction](#introduction)
- [Quick start](#quick-start)
- [Installing](#installing)
- [Examples](#examples)
- [API description](#api-description)

# Introduction

This library provides complete ICQ/Myteam Bot API 1.0 interface and requires Python 3.5+

# Quick start

* Create your own bot by sending the /newbot command to <a href="https://icq.com/people/70001">Metabot</a> and follow the instructions.
    >Note: a bot can only reply after the user has added it to his contact list, or if the user was the first to start a dialogue.
* You can configure the domain that hosts your ICQ server. When instantiating the Bot class, add the address of your domain.
    > Example: Bot(token=TOKEN, url="https://api.icq.net"), by default we use the domain: https://api.icq.net/bot/v1 (ICQ) or http://myteam.mail.ru (VK Teams)

# Installing

Install using pip:
```bash
pip install -U async-icq
```

Install from sources:
```bash
git clone https://github.com/mail-ru-im/bot-python.git
cd async-icq
python setup.py install
```

# Examples

Basic example of using this library will look like this

```python
from async_icq.bot import AsyncBot
from async_icq.events import Event

# Creating bot
example = AsyncBot(
  token='TOKEN',
  url='https://api.icq.net',
)


# Adding some basic event handler by decorators (handler must accept 2 arguments: bot and event)
# Diffent decorators will set it up for diffent types of events
@example.start_handler()
async def hello(bot: AsyncBot, event: Event):
  await bot.send_text(
    chatId=event.from_chat,
    text=f'Hi, {event.message_author["userId"]}'
  )

  await bot.logger.debug(f'Answered to {event.from_chat}')


# Starting to poll new events and sending them to middleware and handlers
example.start_poll()
```

Example of how to use this library could be found in async-icq/examples

# API description
<ul>
    <li><a href="https://icq.com/botapi/">icq.com/botapi/</a></li>
    <li><a href="https://agent.mail.ru/botapi/">agent.mail.ru/botapi/</a></li>
    <li><a href="https://myteam.mail.ru/botapi/">myteam.mail.ru/botapi/</a></li>
</ul>
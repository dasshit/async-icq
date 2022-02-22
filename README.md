# Async ICQ/VK Teams bot API wrapper

[![PyPi Package Version](https://img.shields.io/pypi/v/async_icq)](https://pypi.org/project/async-icq/)
[![PyPi Package Status](https://img.shields.io/pypi/status/async_icq?color=green&label=stable)](https://pypi.org/project/async-icq/)
[![Supported Python versions](https://img.shields.io/pypi/pyversions/async_icq)](https://pypi.org/project/async-icq/)
[![Package dwn stats](https://img.shields.io/pypi/dm/async_icq)](https://pypi.org/project/async-icq/)
[![License](https://img.shields.io/github/license/dasshit/async-icq)](https://pypi.org/project/async-icq/)
[![Repo size](https://img.shields.io/github/repo-size/dasshit/async-icq)](https://pypi.org/project/async-icq/)
[![Author stars count](https://img.shields.io/github/stars/dasshit?style=social)](https://pypi.org/project/async-icq/)

<img src="https://icq.com/botapi/res/logo_icq_new.png" width="40%"><img src="https://myteam.mail.ru/botapi/res/logo_myteam.png" width="40%">

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
    > Example: Bot(token=TOKEN, url="https://api.icq.net"), by default we use the domain: https://api.icq.net (ICQ) or http://myteam.mail.ru (VK Teams)

# Installing

Install using pip:
```bash
pip install -U async-icq
```

Install from sources:
```bash
git clone https://github.com/dasshit/async-icq.git
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
@example.message_handler()
async def hello(event: Event):
  
  await event.answer(
    text=f'Hi, {event.from_.userId}'
  )

  await event.log(
    f'Answered to {event.chat.chatId} to {event.from_.userId}')


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
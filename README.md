# TorioGhost Client Discord Bot

Official Discord bot for the TorioGhost Client community.

A custom Discord bot built with **discord.py 2.0.0** featuring hybrid commands, interactive menus, command restrictions, cooldown systems, i18n multi-language support, and anti-spam protections.

---

# Features

## Commands

* `/ping` — Check bot latency
* `/boosters` — Display current server boosters
* `/members` — Display current server member statistics (Total, Humans, Bots, Online)
* `/features` — Interactive module browser
* `/feature <name>` — Search details for a specific client module
* `/invite` — Join the official Torio Client support server
* `/download` — Download the latest Torio Client release
* `/version` — View all supported Minecraft versions for Torio Client
* `/website` — Get the official Torio Client website link
* `/rules` — Display server rules

## Welcome System

Automatically sends a welcome message whenever a new member joins the server.

* Mentions the joining user
* Displays the user's profile icon
* Shows the user's Discord ID
* Clean and minimal Discord-style embed design
* Configurable welcome channel

## Multi-Language Support (i18n)

Supports automatic language switching based on the user's Discord client language:
* English (`en`)
* 日本語 (`ja`)
* Русский (`ru`)
* Українська (`uk`)
* Español (`es`)

---

# Security / Anti-Spam Systems

## Global Command Cooldown

All users share one cooldown:

* **2 command uses per 1 second**

Prevents spam and command flooding.

---

## Command Channel Restriction

Commands can only be used in the configured bot command channel.

If used elsewhere, users are redirected to the correct channel.

---

## Interactive Menu Protection

The `/features` menu includes:

* Only the command author can use the menu
* 2 second personal interaction cooldown
* Spam click prevention

---

# Project Structure

```text
TorioClientBOT/
├── cogs/
│   ├── client_info.py     # /features, /feature, /download, /version
│   ├── events.py          # on_member_join welcome messages
│   └── general.py         # /ping, /boosters, /members, /invite, /rules, /website
├── locales/
│   ├── en.json
│   ├── es.json
│   ├── ja.json
│   ├── modules.json       # Module definitions & multilingual descriptions
│   ├── ru.json
│   └── uk.json
├── utils/
│   └── i18n.py            # i18n helper & language detector
├── .env
├── main.py                # Bot initialization & Cog loader
├── README.md
└── requirements.txt
```

---

# Built With

* Python 3.10+
* discord.py 2.0.0
* python-dotenv 1.2.2

---

# Installation

## Clone Repository

```bash
git clone https://github.com/Uncle-Awrt/Torio-Client-Bot.git
cd Torio-Client-Bot
```

## Install Dependencies

```bash
pip install -r requirements.txt
```

---

# Environment Variables

Create a `.env` file:

```env
TOKEN=your_bot_token
GUILD_ID=your_server_id
ALLOWED_CHANNEL_ID=your_bot_channel_id
WELCOME_CHANNEL_ID=your_welcome_channel_id
BOTCHANNELID=<#your_bot_channel_id>
TORIOLOGO=<:emoji_name:emoji_id>
SERVERBOOST=<a:emoji_name:emoji_id>
```

---

# Running the Bot

```bash
python main.py
```

---

# License

**MIT License**
# [View License](https://github.com/kukentyan/Torio-Discord-Bot/blob/main/LICENSE)

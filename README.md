# TorioGhost Client Discord Bot

Official Discord bot for the TorioGhost Client community.

A custom Discord bot built with **discord.py 2.0.0** featuring hybrid commands, interactive menus, command restrictions, cooldown systems, and anti-spam protections.

---

# Features

## Commands

* `/ping` — Check bot latency
* `/boosters` — Display current server boosters
* `/features` — Interactive module browser
* `/invite` — Join the official Torio Client support server
* `/download` — Download the latest Torio Client release

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

# Built With

* Python 3.10+
* discord.py 2.0.0

---

# Installation

## Clone Repository

```"
git clone https://github.com/Uncle-Awrt/Torio-Client-Bot.git
cd Torio-Client-Bot
```

## Install Dependencies

```"
pip install discord.py==2.0.0
```

---

# Environment Variables

Create a `.env` file:

```"
TOKEN=your_bot_token
GUILD_ID=your_server_id
ALLOWED_CHANNEL_ID=your_bot_channel_id
BOTCHANNELID=<#your_bot_channel_id>
TORIOLOGO=<:emoji_name:emoji_id>
SERVERBOOST=<a:emoji_name:emoji_id>
```

---

# Running the Bot

```
python main.py
```

---

# Example Commands

```"
/ping
/features
/download
/invite
/boosters
```

---

# Project Structure

```"
main.py
README.md
.env
```

---

# Recommended Hosting

* Raspberry Pi
* Local PC

---

# requirements.txt

```"
discord.py==2.0.0
```

---

# Notes

This bot uses **Hybrid Commands**, meaning slash commands are supported.

Built for private guild/server usage.

---

# License

**MIT License**\
# [View License](https://github.com/kukentyan/Torio-Discord-Bot/blob/main/LICENSE)

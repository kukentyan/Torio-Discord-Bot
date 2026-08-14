import discord
from discord import app_commands
from discord.ext import commands
import os
import time
from dotenv import load_dotenv
from pathlib import Path

load_dotenv(dotenv_path=Path(__file__).parent / ".env")

TOKEN = os.getenv("TOKEN")
GUILD_ID = os.getenv("GUILD_ID")
ALLOWED_CHANNEL_ID = os.getenv("ALLOWED_CHANNEL_ID")
WELCOME_CHANNEL_ID = os.getenv("WELCOME_CHANNEL_ID")
TORIOLOGO = os.getenv("TORIOLOGO")
SERVERBOOST = os.getenv("SERVERBOOST")
BOTCHANNELID = os.getenv("BOTCHANNELID")

intents = discord.Intents.default()
intents.message_content = True
intents.members = True
bot = commands.Bot(command_prefix="!", intents=intents)


global_cooldown = commands.CooldownMapping.from_cooldown(
    2, 1.0, commands.BucketType.default
)

@bot.check
async def global_checks(ctx):
    if ctx.channel.id != int(ALLOWED_CHANNEL_ID):
        await ctx.send(
            f"Use commands in the bot channel only.\n{BOTCHANNELID}",
            ephemeral=True
        )
        return False

    bucket = global_cooldown.get_bucket(ctx.message)
    retry_after = bucket.update_rate_limit()

    if retry_after:
        await ctx.send(
            f"Please wait {retry_after:.1f}s before using another command.",
            ephemeral=True
        )
        return False

    return True

@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.CheckFailure):
        return
    raise error

@bot.event
async def on_ready() -> None:
    await bot.tree.sync(guild=discord.Object(id=GUILD_ID))

    await bot.change_presence(
        status=discord.Status.do_not_disturb,
        activity=discord.Game(name="/download")
    )

    print(f"Logged in as {bot.user}")


@bot.hybrid_command(name="ping", description="ping!")
@app_commands.guilds(discord.Object(id=GUILD_ID))
async def ping(ctx):
    await ctx.send(f"Pong! {round(bot.latency * 1000)}ms")


@bot.hybrid_command(name="boosters", description="Display the list of server boosters")
@app_commands.guilds(discord.Object(id=GUILD_ID))
async def boosters(ctx):
    guild = ctx.guild
    booster_list = guild.premium_subscribers

    embed = discord.Embed(
        title=f"{SERVERBOOST} Server Boosters {SERVERBOOST}",
        color=0x9B59B6
    )

    if not booster_list:
        embed.description = "There are currently no boosters."
    else:
        boosters_text = "\n".join(
            [f"{member.mention} (`{member.name}`)" for member in booster_list]
        )
        embed.description = boosters_text
        booster_count = len(booster_list)
        booster_word = "booster" if booster_count == 1 else "boosters"
        embed.set_footer(text=f"Total {booster_count} {booster_word} • Nitro Boost Tier {guild.premium_tier}")

    await ctx.send(embed=embed)
def get_user_locale(target) -> str:
    """
    Returns 'ja', 'ru', 'uk', 'es', or 'en' based on target's locale (Interaction or Context).
    """
    locale = None
    if isinstance(target, discord.Interaction):
        locale = target.locale
    elif hasattr(target, "interaction") and target.interaction:
        locale = target.interaction.locale

    if locale:
        loc_str = str(locale).lower()
        if loc_str.startswith("ja"):
            return "ja"
        elif loc_str.startswith("ru"):
            return "ru"
        elif loc_str.startswith("uk"):
            return "uk"
        elif loc_str.startswith("es"):
            return "es"
    return "en"


MODULES = {
    # Visual Modules
    "fullbright": {
        "title": "Fullbright",
        "desc_en": "Keeps the world fully illuminated at all times.",
        "desc_ja": "ワールドを常時明るく照らし、暗闇をなくします。",
        "desc_ru": "Освещает мир вокруг вас на максимум в любое время.",
        "desc_uk": "Освітлює світ навколо вас на максимум у будь-який час.",
        "desc_es": "Mantiene el mundo completamente iluminado en todo momento.",
        "category": "Visual Modules"
    },
    "zoom": {
        "title": "Zoom",
        "desc_en": "Adjustable zoom for clearer long-distance vision.",
        "desc_ja": "調整可能なズーム機能で遠くを鮮明に観察できます。",
        "desc_ru": "Регулируемый зум для четкого обзора на дальних расстояниях.",
        "desc_uk": "Регульований зум для чіткого огляду на далеких відстанях.",
        "desc_es": "Zoom ajustable para una visión más clara a larga distancia.",
        "category": "Visual Modules"
    },
    "coordinates": {
        "title": "Coordinates",
        "desc_en": "Displays your current XYZ coordinates on screen.",
        "desc_ja": "画面上に現在のXYZ座標を表示します。",
        "desc_ru": "Отображает ваши текущие координаты XYZ на экране.",
        "desc_uk": "Відображає ваші поточні координати XYZ на екрані.",
        "desc_es": "Muestra tus coordenadas XYZ actuales en pantalla.",
        "category": "Visual Modules"
    },
    "esp": {
        "title": "ESP",
        "desc_en": "Draws a 2D bounding box outline around nearby entities, making them visible through walls.",
        "desc_ja": "近くのエンティティを壁越しに2D枠線で表示します。",
        "desc_ru": "Отображает 2D-контуры вокруг существ сквозь стены.",
        "desc_uk": "Відображає 2D-контури навколо істот крізь стіни.",
        "desc_es": "Dibuja un contorno 2D alrededor de las entidades cercanas, haciéndolas visibles a través de paredes.",
        "category": "Visual Modules"
    },
    "truesight": {
        "title": "TrueSight",
        "desc_en": "Makes all invisible entities fully visible (e.g. invisible players, mobs, or effects).",
        "desc_ja": "透明化状態のプレイヤーやモブ、エフェクトを完全に見えるようにします。",
        "desc_ru": "Делает всех невидимых игроков, мобов и эффекты полностью видимыми.",
        "desc_uk": "Роблять усіх невидимих гравців, мобів та ефекти повністю видимими.",
        "desc_es": "Hace totalmente visibles a todas las entidades invisibles (jugadores, mobs o efectos).",
        "category": "Visual Modules"
    },
    "timechanger": {
        "title": "Time Changer",
        "desc_en": "Freely change the in-game time client-side for better visibility or aesthetics.",
        "desc_ja": "クライアント側で自由に対象のゲーム内時間を変更できます。",
        "desc_ru": "Свободно меняйте время суток на клиенте для лучшей видимости.",
        "desc_uk": "Вільно змінюйте час доби на клієнті для кращої видимості.",
        "desc_es": "Cambia libremente la hora del juego en el cliente para mejor visibilidad o estética.",
        "category": "Visual Modules"
    },
    "duckoverlay": {
        "title": "Duck Overlay",
        "desc_en": "Displays a cute animated duck on your screen to help you stay calm during gameplay.",
        "desc_ja": "画面上にかわいいアヒルのアニメーションを表示しリラックスできます。",
        "desc_ru": "Отображает милую анимированную утку на экране для хорошего настроения.",
        "desc_uk": "Відображає милу анімовану качку на екрані для гарного настрою.",
        "desc_es": "Muestra un lindo pato animado en tu pantalla para mantenerte relajado mientras juegas.",
        "category": "Visual Modules"
    },
    "notifications": {
        "title": "Notifications",
        "desc_en": "Displays in-game notification toasts for client events and toggles.",
        "desc_ja": "クライアントのモジュール切替やイベントの通知を画面上に表示します。",
        "desc_ru": "Отображает игровые уведомления о переключении модулей.",
        "desc_uk": "Відображає ігрові сповіщення про перемикання модулів.",
        "desc_es": "Muestra notificaciones en el juego para eventos del cliente y módulos activados.",
        "category": "Visual Modules"
    },
    "customwatermark": {
        "title": "Custom Watermark",
        "desc_en": "Displays a customizable text watermark on screen with configurable font, size, and text.",
        "desc_ja": "フォントやサイズ、テキストを自由にカスタマイズできるウォーターマークを表示します。",
        "desc_ru": "Отображает настраиваемый текстовый водяной знак на экране.",
        "desc_uk": "Відображає налаштовуваний текстовий водяний знак на екрані.",
        "desc_es": "Muestra una marca de agua de texto personalizable en pantalla.",
        "category": "Visual Modules"
    },
    "arraylist": {
        "title": "Array List",
        "desc_en": "Displays a list of currently active modules on screen as an in-game overlay.",
        "desc_ja": "現在有効化されているモジュールの一覧を画面上でオーバーレイ表示します。",
        "desc_ru": "Отображает список всех активных модулей на экране.",
        "desc_uk": "Відображає список усіх активних модулів на екрані.",
        "desc_es": "Muestra una lista de los módulos actualmente activos en pantalla.",
        "category": "Visual Modules"
    },

    # Combat Modules
    "reach": {
        "title": "Reach (Randomizer Support)",
        "desc_en": "Extends melee attack distance.",
        "desc_ja": "近接攻撃の届く距離を拡張します。",
        "desc_ru": "Увеличивает дистанцию ближней атаки.",
        "desc_uk": "Збільшує дистанцію ближньої атаки.",
        "desc_es": "Extiende la distancia de ataque cuerpo a cuerpo.",
        "category": "Combat Modules"
    },
    "autoclicker": {
        "title": "AutoClicker (Left & Right) (Randomizer Support)",
        "desc_en": "Automates left and right clicks. Menu Check and Block Break Check can be toggled individually via checkboxes.",
        "desc_ja": "左右の連打を自動化します。メニュー開閉チェックやブロック破壊チェックも個別に設定可能。",
        "desc_ru": "Автоматизирует левый и правый клик с проверкой меню и ломания блоков.",
        "desc_uk": "Автоматизує лівий та правий клік із перевіркою меню та ламання блоків.",
        "desc_es": "Automatiza los clics izquierdo y derecho con verificación de menú y rotura de bloques.",
        "category": "Combat Modules"
    },
    "doubleclicker": {
        "title": "Double Clicker",
        "desc_en": "Simulates a double click on each real mouse click, effectively doubling your CPS.",
        "desc_ja": "1回のクリックに対してダブルクリックを発生させ、CPSを実質倍増させます。",
        "desc_ru": "Имитирует двойной клик при каждом нажатии, удваивая ваш CPS.",
        "desc_uk": "Імітує подвійний клік при кожному натисканні, подвоюючи ваш CPS.",
        "desc_es": "Simula un doble clic con cada clic real del ratón, duplicando eficazmente tu CPS.",
        "category": "Combat Modules"
    },
    "hitbox": {
        "title": "Hitbox",
        "desc_en": "Expands entity hitboxes for easier targeting.",
        "desc_ja": "ターゲットしやすいようエンティティのヒットボックスを拡張します。",
        "desc_ru": "Увеличивает хитбоксы существ для более легкого попадания.",
        "desc_uk": "Збільшує хітбокси істот для легшого влучання.",
        "desc_es": "Expande las cajas de colisión de las entidades para apuntar más fácilmente.",
        "category": "Combat Modules"
    },
    "triggerbot": {
        "title": "TriggerBot (CPS Randomizer Support)",
        "desc_en": "Automatically attacks when your crosshair is over a target. Supports **First Hit**, **Auto Click**, and **HitSelect** mode.",
        "desc_ja": "レティクルが敵に重なった時に自動攻撃します。First Hit, Auto Click, HitSelect モードに対応。",
        "desc_ru": "Автоматически атакует, когда прицел наведен на цель. Поддерживает First Hit, Auto Click и HitSelect.",
        "desc_uk": "Автоматично атакує, коли приціл наведено на ціль. Підтримує First Hit, Auto Click та HitSelect.",
        "desc_es": "Ataca automáticamente cuando la retícula está sobre un objetivo. Soporta First Hit, Auto Click y HitSelect.",
        "category": "Combat Modules"
    },
    "stickyaim": {
        "title": "Sticky Aim (Randomizer Support)",
        "desc_en": "*(Previously Micro Aim)* Automatically fine-tunes your sensitivity when manually aiming at an enemy, helping your aim lock on smoothly.",
        "desc_ja": "*(旧 Micro Aim)* 敵エイム時に感度を自動調整し、スムーズなロックオンをアシストします。",
        "desc_ru": "*(Ранее Micro Aim)* Автоматически плавно подстраивает чувствительность при прицеливании на врага.",
        "desc_uk": "*(Раніше Micro Aim)* Автоматично плавно підлаштовує чутливість при прицілюванні на ворога.",
        "desc_es": "*(Antes Micro Aim)* Ajusta automáticamente tu sensibilidad al apuntar a un enemigo.",
        "category": "Combat Modules"
    },
    "aimassist": {
        "title": "Aim Assist",
        "desc_en": "Guides your aim toward nearby **Players**. Dynamic Yaw/Pitch calculations ensure smooth, jitter-free tracking.",
        "desc_ja": "近くのプレイヤーにエイムを誘導します。動的なYaw/Pitch計算によりブレのない追尾を実現。",
        "desc_ru": "Плавно наводит ваш прицел на ближайших игроков без рывков.",
        "desc_uk": "Плавно наводить ваш приціл на найближчих гравців без ривків.",
        "desc_es": "Guía suavemente tu puntería hacia los jugadores cercanos sin tirones.",
        "category": "Combat Modules"
    },
    "backtrack": {
        "title": "BackTrack",
        "desc_en": "Delays incoming player position packets using a smooth continuous delay queue, allowing you to hit enemies from where they were moments ago.",
        "desc_ja": "敵の位置パケットを遅延させ、過去の敵の位置を攻撃できるようにします。Flow / Hold モード対応。",
        "desc_ru": "Задерживает пакеты позиций игроков, позволяя попадать по врагам в их прошлых позициях.",
        "desc_uk": "Затримує пакети позицій гравців, дозволяючи влучати по ворогах у їхніх минулих позиціях.",
        "desc_es": "Retrasa los paquetes de posición de los jugadores para golpearlos en sus posiciones pasadas.",
        "category": "Combat Modules"
    },
    "autothrow": {
        "title": "Auto Throw *(Macro)*",
        "desc_en": "Automated pearl, snowball, and item throw macro.",
        "desc_ja": "エンダーパールや雪玉、アイテム投げを自動化するマクロ。",
        "desc_ru": "Автоматический макрос для броска жемчуга, снежков и предметов.",
        "desc_uk": "Автоматичний макрос для кидка перлів, сніжок та предметів.",
        "desc_es": "Macro automatizado para lanzar perlas, bolas de nieve u objetos.",
        "category": "Combat Modules"
    },
    "autobow": {
        "title": "Auto Bow *(Macro)*",
        "desc_en": "Automated bow charge macro.",
        "desc_ja": "弓のチャージを自動化するマクロ。",
        "desc_ru": "Автоматический макрос для натяжения лука.",
        "desc_uk": "Автоматичний макрос для натягування лука.",
        "desc_es": "Macro automatizado para cargar el arco.",
        "category": "Combat Modules"
    },

    # Movement Modules
    "togglesprint": {
        "title": "Toggle Sprint",
        "desc_en": "Sprint without holding the sprint key.",
        "desc_ja": "ダッシュキーを押し続けなくても自動でダッシュ状態を維持します。",
        "desc_ru": "Бег без необходимости удерживать клавишу спринта.",
        "desc_uk": "Біг без потреби утримувати клавішу спринту.",
        "desc_es": "Corre automáticamente sin necesidad de mantener presionada la tecla de esprintar.",
        "category": "Movement Modules"
    },
    "airacceleration": {
        "title": "Air Acceleration (Randomizer Support)",
        "desc_en": "Allows you to modify acceleration while jumping.",
        "desc_ja": "ジャンプ中の空中移動加速度を調整できます。",
        "desc_ru": "Позволяет изменять ускорение персонажа во время прыжка.",
        "desc_uk": "Дозволяє змінювати прискорення персонажа під час стрибка.",
        "desc_es": "Permite modificar la aceleración mientras saltas.",
        "category": "Movement Modules"
    },
    "timer": {
        "title": "Timer (Randomizer Support)",
        "desc_en": "Allows you to modify the game's tick speed.",
        "desc_ja": "ゲームのティックスピード（進行速度）を変更できます。",
        "desc_ru": "Изменяет скорость игровых тиков (скорость игры).",
        "desc_uk": "Змінює швидкість ігрових тіків (швидкість гри).",
        "desc_es": "Modifica la velocidad de los ticks del juego.",
        "category": "Movement Modules"
    },
    "autojumpreset": {
        "title": "Auto JumpReset (Randomizer Support)",
        "desc_en": "Automates jump reset timing during combat.",
        "desc_ja": "戦闘中のジャンプリセットのタイミングを自動化します。",
        "desc_ru": "Автоматизирует тайминг джамп-ресета во время боя.",
        "desc_uk": "Автоматизує таймінг джамп-ресету під час бою.",
        "desc_es": "Automatiza el tiempo de salto (jump reset) durante el combate.",
        "category": "Movement Modules"
    },
    "lagswitch": {
        "title": "Lag Switch",
        "desc_en": "Hold the configured keybind to freeze outgoing packets and simulate lag.",
        "desc_ja": "キーを押している間、送信パケットを停止してラグを発生させます。",
        "desc_ru": "Удерживайте клавишу для задержки исходящих пакетов и создания лага.",
        "desc_uk": "Утримуйте клавішу для затримки вихідних пакетів та створення лагу.",
        "desc_es": "Mantén presionada la tecla configurada para congelar los paquetes salientes y simular lag.",
        "category": "Movement Modules"
    },
    "velocity": {
        "title": "Velocity",
        "desc_en": "Reduces or prevents knockback from attacks with customizable Horizontal (X/Z) and Vertical (Y) multipliers.",
        "desc_ja": "被弾時のノックバックを軽減・無効化します。水平・垂直の倍率を個別に設定可能。",
        "desc_ru": "Уменьшает или полностью отменяет отбрасывание с настройкой по X/Z и Y.",
        "desc_uk": "Зменшує або повністю скасовує відкидання з налаштуванням по X/Z та Y.",
        "desc_es": "Reduce o anula el empuje por ataques con multiplicadores personalizados en X/Z e Y.",
        "category": "Movement Modules"
    },
    "noslowdown": {
        "title": "NoSlowdown",
        "desc_en": "Disables movement slowdown effects when consuming items, using weapons, or traversing slowing terrain.",
        "desc_ja": "アイテム使用時や減速地形による移動速度の低下を無効化します。",
        "desc_ru": "Убирает замедление при использовании предметов, еды и ходьбе по замедляющим блокам.",
        "desc_uk": "Прибирає сповільнення при використанні предметів, їжі та ходьбі по сповільнюючих блоках.",
        "desc_es": "Elimina la ralentización al consumir objetos, usar armas o caminar en terreno lento.",
        "category": "Movement Modules"
    },

    # Utility & Settings
    "guisettings": {
        "title": "GUI Settings",
        "desc_en": "Customize the look of Torio-Client with full RGB accent color control, Light Mode / Dark Mode toggles, and reset capabilities.",
        "desc_ja": "RGBカラー指定、ライト/ダークモード切替など Torio-Client の見た目をカスタマイズできます。",
        "desc_ru": "Настройка внешнего вида Torio-Client: RGB-цвета, светлая/тёмная тема.",
        "desc_uk": "Налаштування зовнішнього вигляду Torio-Client: RGB-кольори, світла/темна тема.",
        "desc_es": "Personaliza la apariencia de Torio-Client: colores RGB, modo claro/oscuro.",
        "category": "Utility & Settings"
    },
    "ingameoverlay": {
        "title": "Ingame Overlay",
        "desc_en": "Switch between rendering the GUI as an external window or as a seamless in-game overlay.",
        "desc_ja": "GUIの描画を外部ウィンドウ方式かインゲームオーバーレイ方式か切替できます。",
        "desc_ru": "Переключение между внешним окном GUI и внутриигровым оверлеем.",
        "desc_uk": "Перемикання між зовнішнім вікном GUI та всерединігровим оверлеєм.",
        "desc_es": "Cambia entre ventana externa de GUI o superposición en el juego.",
        "category": "Utility & Settings"
    },
    "fakelag": {
        "title": "FakeLag",
        "desc_en": "*(Previously Reverse BackTrack)* Delays your own movement packets sent to the server, making your character appear to stutter or lag to other players.",
        "desc_ja": "*(旧 Reverse BackTrack)* 自身の移動パケットを遅延させ、相手から見てラグっているように見せかけます。",
        "desc_ru": "*(Ранее Reverse BackTrack)* Задерживает ваши пакеты движения, создавая видимость лагов для других.",
        "desc_uk": "*(Раніше Reverse BackTrack)* Затримує ваші пакети руху, створюючи видимість лагів для інших.",
        "desc_es": "*(Antes Reverse BackTrack)* Retrasa tus paquetes de movimiento para simular lag ante otros jugadores.",
        "category": "Utility & Settings"
    },
    "blink": {
        "title": "Blink",
        "desc_en": "Temporarily queues outgoing network packets while holding a keybind (Reverse Hold), instantly teleporting your position upon release.",
        "desc_ja": "キーを押している間パケットを溜め込み、離した瞬間にワープしたように見せかけます。",
        "desc_ru": "Накапливает пакеты при удержании клавиши, мгновенно телепортируя вас при отпускании.",
        "desc_uk": "Накопичує пакети при утримуванні клавіші, миттєво телепортуючи вас при відпусканні.",
        "desc_es": "Acumula paquetes al mantener una tecla, teletransportándote al soltarla.",
        "category": "Utility & Settings"
    },
    "fastitem": {
        "title": "Fast Item",
        "desc_en": "Speeds up item use timers, allowing faster item usage.",
        "desc_ja": "アイテムの使用タイマーを加速させ、素早い使用を可能にします。",
        "desc_ru": "Ускоряет таймер использования предметов.",
        "desc_uk": "Прискорює таймер використання предметів.",
        "desc_es": "Acelera el temporizador de uso de objetos.",
        "category": "Utility & Settings"
    },
    "streamprotect": {
        "title": "Streamprotect",
        "desc_en": "Hides sensitive or personal information while streaming.",
        "desc_ja": "配信や画面共有時に Torio-Client や個人情報を非表示にします。",
        "desc_ru": "Скрывает клиент Torio и личную информацию во время стрима или трансляции.",
        "desc_uk": "Приховує клієнт Torio та особисту інформацію під час стріму чи трансляції.",
        "desc_es": "Oculta información personal o el cliente mientras transmites en vivo.",
        "category": "Utility & Settings"
    },
    "systemtray": {
        "title": "System Tray",
        "desc_en": "Minimize Torio-Client to the system tray and reopen it at any time.",
        "desc_ja": "Torio-Client をシステムトレイに最小化し、いつでも再呼び出しできます。",
        "desc_ru": "Сворачивает Torio-Client в системный трей.",
        "desc_uk": "Згортає Torio-Client у системний трей.",
        "desc_es": "Minimiza Torio-Client a la bandeja del sistema.",
        "category": "Utility & Settings"
    },
    "discordpresence": {
        "title": "Discord Presence",
        "desc_en": "Displays your current menu, server, Minecraft version, and client status on Discord.",
        "desc_ja": "現在のサーバーやバージョンなどのプレイ状況を Discord Rich Presence に表示します。",
        "desc_ru": "Отображает ваш статус, сервер и версию Minecraft в Discord Presence.",
        "desc_uk": "Відображає ваш статус, сервер та версію Minecraft у Discord Presence.",
        "desc_es": "Muestra tu estado, servidor y versión de Minecraft en Discord Presence.",
        "category": "Utility & Settings"
    },
    "togglesounds": {
        "title": "Toggle Sounds",
        "desc_en": "Plays a sound effect when toggling modules on or off. Can be easily enabled or disabled.",
        "desc_ja": "モジュールのオン/オフ切り替え時に効果音を再生します。",
        "desc_ru": "Воспроизводит звуковой эффект при включении/выключении модулей.",
        "desc_uk": "Відтворює звуковий ефект при увімкненні/вимкненні модулів.",
        "desc_es": "Reproduce un efecto de sonido al activar/desactivar módulos.",
        "category": "Utility & Settings"
    },
    "deviceidspoofer": {
        "title": "Device ID Spoofer",
        "desc_en": "Spoofs your device ID to help protect your identity. Can be configured to spoof on join, on startup, or both.",
        "desc_ja": "デバイスIDを偽装し、識別を防止します。起動時・参加時の設定が可能。",
        "desc_ru": "Спуфинг ID устройства для защиты конфиденциальности.",
        "desc_uk": "Спуфінг ID пристрою для захисту конфіденційності.",
        "desc_es": "Falsifica tu ID de dispositivo para proteger tu privacidad.",
        "category": "Utility & Settings"
    },
    "auto360": {
        "title": "Auto 360 *(Macro)*",
        "desc_en": "Automated 360° spin macro. Supports Right, Left, and Alternate spin directions with configurable sensitivity and keybind.",
        "desc_ja": "視点を自動で360度回転させるマクロ。左右および交互の回転方向に対応。",
        "desc_ru": "Автоматический макрос вращения на 360°. Поддерживает вращение вправо, влево и поочередно.",
        "desc_uk": "Автоматичний макрос обертання на 360°. Підтримує обертання вправо, вліво та по черзі.",
        "desc_es": "Macro automatizado de giro en 360°. Soporta giro a la derecha, izquierda y alternado.",
        "category": "Utility & Settings"
    },
}

FEATURES_TEXT = {
    "ja": {
        "title": "Torio Client — 機能一覧",
        "description": "下のドロップダウンメニューからカテゴリを選択してモジュールの詳細を確認できます。\nまたは `/feature <モジュール名>` で特定のモジュールを検索できます。",
        "cat_visual": "Visual Modules (ビジュアル)",
        "cat_combat": "Combat Modules (コンバット)",
        "cat_movement": "Movement Modules (ムーブメント)",
        "cat_utility": "Utility & Settings (ユーティリティ & 設定)",
        "cat_select_ph": "モジュールのカテゴリを選択...",
        "mod_select_ph": "詳細を見るモジュールを選択...",
        "available_mods": "**利用可能なモジュール:**",
        "select_below": "下のドロップダウンからモジュールを選択して詳細を表示できます。"
    },
    "ru": {
        "title": "Torio Client — Список функций",
        "description": "Выберите категорию из выпадающего меню ниже, чтобы просмотреть сведения о модуле.\nИли используйте `/feature <название>`, чтобы найти конкретный модуль.",
        "cat_visual": "Визуальные модули (Visual)",
        "cat_combat": "Боевые модули (Combat)",
        "cat_movement": "Модули движения (Movement)",
        "cat_utility": "Утилиты и Настройки (Utility)",
        "cat_select_ph": "Выберите категорию модулей...",
        "mod_select_ph": "Выберите модуль для подробностей...",
        "available_mods": "**Доступные модули:**",
        "select_below": "Выберите модуль из выпадающего списка ниже для подробностей."
    },
    "uk": {
        "title": "Torio Client — Список функцій",
        "description": "Оберіть категорію з випадного меню нижче, щоб переглянути деталі модуля.\nАбо використовуйте `/feature <назва>`, щоб знайти конкретний модуль.",
        "cat_visual": "Візуальні модули (Visual)",
        "cat_combat": "Бойові модули (Combat)",
        "cat_movement": "Модулі руху (Movement)",
        "cat_utility": "Утиліти та Налаштування (Utility)",
        "cat_select_ph": "Оберіть категорію модулів...",
        "mod_select_ph": "Оберіть модуль для деталей...",
        "available_mods": "**Доступні модулі:**",
        "select_below": "Оберіть модуль із випадного списку нижче для деталей."
    },
    "es": {
        "title": "Torio Client — Características",
        "description": "Selecciona una categoría en el menú desplegable de abajo para ver los detalles del módulo.\nO usa `/feature <nombre>` para buscar un módulo específico.",
        "cat_visual": "Módulos Visuales (Visual)",
        "cat_combat": "Módulos de Combate (Combat)",
        "cat_movement": "Módulos de Movimiento (Movement)",
        "cat_utility": "Utilidad y Ajustes (Utility)",
        "cat_select_ph": "Selecciona una categoría de módulos...",
        "mod_select_ph": "Selecciona un módulo para ver detalles...",
        "available_mods": "**Módulos Disponibles:**",
        "select_below": "Selecciona un módulo en el menú desplegable para más detalles."
    },
    "en": {
        "title": "Torio Client — Features",
        "description": "Select a category from the dropdown menu to view module details.\nOr use `/feature <name>` to search for a specific module.",
        "cat_visual": "Visual Modules",
        "cat_combat": "Combat Modules",
        "cat_movement": "Movement Modules",
        "cat_utility": "Utility & Settings",
        "cat_select_ph": "Select a module category...",
        "mod_select_ph": "Select a module in this category...",
        "available_mods": "**Available Modules:**",
        "select_below": "Select a module from the dropdown below for details."
    }
}


class CategoryModuleSelect(discord.ui.Select):
    def __init__(self, category="Visual Modules", locale="en"):
        self.category = category
        self.user_locale = locale
        options = []
        for key, info in MODULES.items():
            if info["category"] == category:
                label = info["title"].replace("*", "")
                options.append(
                    discord.SelectOption(
                        label=label[:100],
                        description=category[:100],
                        value=key
                    )
                )
        ph = FEATURES_TEXT[locale]["mod_select_ph"]
        super().__init__(placeholder=ph, options=options, row=1)

    async def callback(self, interaction: discord.Interaction):
        selected = self.values[0]
        info = MODULES[selected]
        locale = get_user_locale(interaction)

        desc = info.get(f"desc_{locale}", info["desc_en"])

        embed = discord.Embed(
            title=info["title"],
            description=desc,
            color=0x5865F2
        )
        embed.set_footer(text=info["category"])

        await interaction.response.edit_message(embed=embed, view=self.view)


class CategorySelect(discord.ui.Select):
    def __init__(self, locale="en"):
        self.user_locale = locale
        t = FEATURES_TEXT[locale]
        options = [
            discord.SelectOption(label=t["cat_visual"], description="Fullbright, Zoom, ESP, TrueSight, etc.", value="Visual Modules"),
            discord.SelectOption(label=t["cat_combat"], description="Reach, AutoClicker, Hitbox, Aim Assist, etc.", value="Combat Modules"),
            discord.SelectOption(label=t["cat_movement"], description="Toggle Sprint, Velocity, Lag Switch, etc.", value="Movement Modules"),
            discord.SelectOption(label=t["cat_utility"], description="GUI Settings, Ingame Overlay, FakeLag, etc.", value="Utility & Settings"),
        ]
        super().__init__(placeholder=t["cat_select_ph"], options=options, row=0)

    async def callback(self, interaction: discord.Interaction):
        selected_category = self.values[0]
        locale = get_user_locale(interaction)
        t = FEATURES_TEXT[locale]

        category_modules = [info["title"].replace("*", "") for info in MODULES.values() if info["category"] == selected_category]
        modules_text = ", ".join(category_modules)

        embed = discord.Embed(
            title=f"Torio Client — {selected_category}",
            description=f"{t['available_mods']}\n{modules_text}\n\n{t['select_below']}",
            color=0x5865F2
        )

        self.view.clear_items()
        self.view.add_item(CategorySelect(locale))
        self.view.add_item(CategoryModuleSelect(selected_category, locale))

        await interaction.response.edit_message(embed=embed, view=self.view)


class FeatureView(discord.ui.View):
    def __init__(self, author_id, current_category="Visual Modules", locale="en"):
        super().__init__(timeout=None)
        self.author_id = author_id
        self.cooldowns = {}

        self.add_item(CategorySelect(locale))
        self.add_item(CategoryModuleSelect(current_category, locale))

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id != self.author_id:
            await interaction.response.send_message(
                "This menu can only be used by the person who ran the command.",
                ephemeral=True
            )
            return False

        user_id = interaction.user.id
        now = time.time()
        last = self.cooldowns.get(user_id, 0)

        if now - last < 2:
            wait = round(2 - (now - last), 1)
            await interaction.response.send_message(
                f"Please wait {wait}s before using the menu again.",
                ephemeral=True
            )
            return False

        self.cooldowns[user_id] = now
        return True


@bot.hybrid_command(name="features", description="Display all features of Torio Client")
@app_commands.guilds(discord.Object(id=GUILD_ID))
async def features(ctx):
    locale = get_user_locale(ctx)
    t = FEATURES_TEXT[locale]

    embed = discord.Embed(
        title=t["title"],
        description=t["description"],
        color=0x5865F2
    )

    visuals = ", ".join([m["title"].replace("*", "") for m in MODULES.values() if m["category"] == "Visual Modules"])
    combats = ", ".join([m["title"].replace("*", "") for m in MODULES.values() if m["category"] == "Combat Modules"])
    movements = ", ".join([m["title"].replace("*", "") for m in MODULES.values() if m["category"] == "Movement Modules"])
    utilities = ", ".join([m["title"].replace("*", "") for m in MODULES.values() if m["category"] == "Utility & Settings"])

    embed.add_field(name=t["cat_visual"], value=visuals, inline=False)
    embed.add_field(name=t["cat_combat"], value=combats, inline=False)
    embed.add_field(name=t["cat_movement"], value=movements, inline=False)
    embed.add_field(name=t["cat_utility"], value=utilities, inline=False)

    await ctx.send(embed=embed, view=FeatureView(ctx.author.id, locale=locale))


async def feature_autocomplete(
    interaction: discord.Interaction,
    current: str,
) -> list[app_commands.Choice[str]]:
    choices = []
    for key, info in MODULES.items():
        title = info["title"].replace("*", "")
        if current.lower() in key or current.lower() in title.lower():
            choices.append(app_commands.Choice(name=title, value=key))
    return choices[:25]


@bot.hybrid_command(name="feature", description="Search details for a specific module of Torio Client")
@app_commands.guilds(discord.Object(id=GUILD_ID))
@app_commands.autocomplete(module=feature_autocomplete)
async def feature(ctx, module: str):
    locale = get_user_locale(ctx)
    module_key = module.lower().replace(" ", "")
    info = MODULES.get(module_key)

    if not info:
        for key, val in MODULES.items():
            if module_key in key or module_key in val["title"].lower():
                info = val
                break

    if not info:
        not_found_msg = {
            "ja": f"モジュール `{module}` が見つかりませんでした。`/features` で一覧を確認してください。",
            "ru": f"Модуль `{module}` не найден. Используйте `/features` для просмотра всех модулей.",
            "uk": f"Модуль `{module}` не знайдено. Використовуйте `/features` для перегляду всіх модулів.",
            "es": f"Módulo `{module}` no encontrado. Usa `/features` para ver todos los módulos.",
            "en": f"Module `{module}` not found. Use `/features` to see all modules."
        }
        await ctx.send(not_found_msg[locale], ephemeral=True)
        return

    desc = info.get(f"desc_{locale}", info["desc_en"])

    embed = discord.Embed(
        title=info["title"],
        description=desc,
        color=0x5865F2
    )
    embed.set_footer(text=info["category"])
    await ctx.send(embed=embed)


@bot.hybrid_command(name="invite", description="Get the invite link for the Torio Client support server")
@app_commands.guilds(discord.Object(id=GUILD_ID))
async def invite(ctx):
    embed = discord.Embed(
        title="Join the TorioGhost Client Server!",
        description="Get support, report bugs, \nand connect with other users in our official Discord server.",
        color=0x5865F2
    )
    embed.add_field(name="Invite Link https://discord.gg/xq8sWQhuXG", value="**[Join Here](https://discord.gg/xq8sWQhuXG)**", inline=False)

    await ctx.send(embed=embed)


DOWNLOAD_TEXT = {
    "ja": {
        "title": f"Download Torio Client{TORIOLOGO}",
        "description": "以下のリンクをクリックして、Torio Client の最新リリースをダウンロードしてください。"
    },
    "ru": {
        "title": f"Download Torio Client{TORIOLOGO}",
        "description": "Нажмите на ссылку ниже, чтобы скачать последний релиз Torio Client."
    },
    "uk": {
        "title": f"Завантажити Torio Client{TORIOLOGO}",
        "description": "Натисніть на посилання нижче, щоб завантажити останній реліз Torio Client."
    },
    "es": {
        "title": f"Descargar Torio Client{TORIOLOGO}",
        "description": "Haz clic en el enlace de abajo para descargar la última versión de Torio Client."
    },
    "en": {
        "title": f"Download Torio Client{TORIOLOGO}",
        "description": "Click the link below to download the latest release of the Torio Client."
    }
}

@bot.hybrid_command(name="download", description="Get the download link for the Torio Client")
@app_commands.guilds(discord.Object(id=GUILD_ID))
async def download(ctx):
    locale = get_user_locale(ctx)
    t = DOWNLOAD_TEXT[locale]

    embed = discord.Embed(
        title=t["title"],
        description=t["description"],
        color=0x5865F2
    )
    embed.add_field(name="GitHub Releases", value="**[Download Here](https://github.com/Uncle-Awrt/Torio-Client/releases)**", inline=False)

    await ctx.send(embed=embed)


VERSION_TEXT = {
    "ja": {
        "title": "Torio Client — バージョン情報",
        "description": "Torio Client がサポートしている Minecraft Bedrock バージョン一覧です。",
        "field": "対応 Bedrock バージョン"
    },
    "ru": {
        "title": "Torio Client — Информация о версиях",
        "description": "Вот поддерживаемые версии Minecraft Bedrock для Torio Client.",
        "field": "Поддерживаемые версии Bedrock"
    },
    "uk": {
        "title": "Torio Client — Інформація про версії",
        "description": "Ось підтримувані версії Minecraft Bedrock для Torio Client.",
        "field": "Підтримувані версії Bedrock"
    },
    "es": {
        "title": "Torio Client — Información de Versiones",
        "description": "Aquí están las versiones de Minecraft Bedrock compatibles con Torio Client.",
        "field": "Versiones Compatibles de Bedrock"
    },
    "en": {
        "title": "Torio Client — Version Information",
        "description": "Here are the supported Minecraft versions for the Torio Client.",
        "field": "Supported Bedrock Versions"
    }
}

@bot.hybrid_command(name="version", description="Look at what version of Minecraft Torio Client Supports")
@app_commands.guilds(discord.Object(id=GUILD_ID))
async def version(ctx):
    locale = get_user_locale(ctx)
    t = VERSION_TEXT[locale]

    embed = discord.Embed(
        title=t["title"],
        description=t["description"],
        color=0x5865F2
    )
    embed.add_field(name=t["field"], value="26.0, 26.1, 26.2, 26.3, 26.10, 26.11, 26.12, 26.13, 26.20, 26.21, 26.30, 26.31, 26.32, 26.33, 26.40, 26.42", inline=False)

    await ctx.send(embed=embed)


WEBSITE_TEXT = {
    "ja": {
        "title": "Torio Client — 公式ウェブサイト",
        "description": "以下のリンクから Torio Client の公式ウェブサイトにアクセスできます。",
        "button": "ウェブサイトを見る"
    },
    "ru": {
        "title": "Torio Client — Официальный сайт",
        "description": "Перейдите по ссылке ниже, чтобы посетить официальный сайт Torio Client.",
        "button": "Посетить сайт"
    },
    "uk": {
        "title": "Torio Client — Офіційний сайт",
        "description": "Перейдіть за посиланням нижче, щоб відвідати офіційний сайт Torio Client.",
        "button": "Відвідати сайт"
    },
    "es": {
        "title": "Torio Client — Sitio Web Oficial",
        "description": "Haz clic en el enlace de abajo para visitar el sitio web oficial de Torio Client.",
        "button": "Visitar Sitio Web"
    },
    "en": {
        "title": "Torio Client — Official Website",
        "description": "Click the link below to visit the official Torio Client website.",
        "button": "Visit Website"
    }
}


class WebsiteView(discord.ui.View):
    def __init__(self, button_label: str):
        super().__init__()
        self.add_item(discord.ui.Button(
            label=button_label,
            url="https://uncle-awrt.github.io/Torio-Client-Website/",
            style=discord.ButtonStyle.link
        ))


@bot.hybrid_command(name="website", description="Get the official website link for Torio Client")
@app_commands.guilds(discord.Object(id=GUILD_ID))
async def website(ctx):
    locale = get_user_locale(ctx)
    t = WEBSITE_TEXT[locale]

    embed = discord.Embed(
        title=t["title"],
        description=t["description"],
        color=0x5865F2
    )
    embed.add_field(
        name="Official Website",
        value="**[uncle-awrt.github.io/Torio-Client-Website](https://uncle-awrt.github.io/Torio-Client-Website/)**",
        inline=False
    )

    await ctx.send(embed=embed, view=WebsiteView(t["button"]))


RULES_TEXT = {
    "ja": {
        "title": "Torio Client サーバー — 公式ルール",
        "description": "みんなが安全で快適に過ごせるよう、以下のコミュニティルールをよく読んで守ってください。",
        "field_name": "Server Rules",
        "rules": (
            "1️⃣ **すべての人に対して敬意を払いましょう。**\n"
            "2️⃣ **嫌がらせ、いじめ、ヘイトスピーチは禁止です。**\n"
            "3️⃣ **スパムや過度な自己宣伝は禁止です。**\n"
            "4️⃣ **適切なコンテンツを維持してください（NSFWや不快な内容は禁止）。**\n"
            "5️⃣ **Discordの利用規約に従ってください。**\n"
            "6️⃣ **個人情報を共有しないでください。**\n"
            "7️⃣ **スタッフの指示に従ってください。**"
        ),
        "footer": "サーバーの安全で快適な環境維持にご協力ありがとうございます！"
    },
    "ru": {
        "title": "Сервер Torio Client — Официальные правила",
        "description": "Пожалуйста, прочтите и соблюдайте наши правила сообщества, чтобы обеспечить безопасную и дружелюбную атмосферу для всех.",
        "field_name": "Server Rules",
        "rules": (
            "1️⃣ **Относитесь ко всем с уважением.**\n"
            "2️⃣ **Никаких домогательств, травли или языка ненависти.**\n"
            "3️⃣ **Никакого спама и излишней саморекламы.**\n"
            "4️⃣ **Сохраняйте приемлемый контент (без NSFW и неприемлемых материалов).**\n"
            "5️⃣ **Соблюдайте Условия использования Discord.**\n"
            "6️⃣ **Не делитесь личной информацией.**\n"
            "7️⃣ **Слушайте администрацию и следуйте их указаниям.**"
        ),
        "footer": "Спасибо за поддержание безопасности и комфорта на нашем сервере!"
    },
    "uk": {
        "title": "Сервер Torio Client — Офіційні правила",
        "description": "Будь ласка, прочитайте та дотримуйтесь наших правил спільноти, щоб забезпечити безпечну та дружню атмосферу для всіх.",
        "field_name": "Правила сервера",
        "rules": (
            "1️⃣ **Ставтеся до всіх з повагою.**\n"
            "2️⃣ **Жодного цькування, булінгу чи мови ненависті.**\n"
            "3️⃣ **Жодного спаму чи надмірної самореклами.**\n"
            "4️⃣ **Зберігайте прийнятний контент (без NSFW та неналежних матеріалів).**\n"
            "5️⃣ **Дотримуйтесь Умов використання Discord.**\n"
            "6️⃣ **Не діліться особистою інформацією.**\n"
            "7️⃣ **Слухайте адміністрацію та дотримуйтесь їхніх вказівок.**"
        ),
        "footer": "Дякуємо за підтримку безпеки та комфорту на нашому сервері!"
    },
    "es": {
        "title": "Servidor de Torio Client — Reglas Oficiales",
        "description": "Por favor, lee y sigue las reglas de nuestra comunidad para garantizar un entorno seguro y agradable para todos.",
        "field_name": "Reglas del Servidor",
        "rules": (
            "1️⃣ **Sé respetuoso con todos.**\n"
            "2️⃣ **Sin acoso, bullying ni discursos de odio.**\n"
            "3️⃣ **Sin spam ni autopromoción excesiva.**\n"
            "4️⃣ **Mantén el contenido apropiado — sin NSFW ni contenido perturbador.**\n"
            "5️⃣ **Sigue los Términos de Servicio de Discord.**\n"
            "6️⃣ **No compartas información personal.**\n"
            "7️⃣ **Escucha al personal y sigue sus instrucciones.**"
        ),
        "footer": "¡Gracias por mantener nuestro servidor seguro y agradable!"
    },
    "en": {
        "title": "Torio Client Server — Official Rules",
        "description": "Please read and follow our community rules to ensure a safe and friendly environment for everyone.",
        "field_name": "Server Rules",
        "rules": (
            "1️⃣ **Be respectful to everyone.**\n"
            "2️⃣ **No harassment, bullying, or hate speech.**\n"
            "3️⃣ **No spamming or excessive self-promotion.**\n"
            "4️⃣ **Keep content appropriate—no NSFW or disturbing content.**\n"
            "5️⃣ **Follow Discord's Terms of Service.**\n"
            "6️⃣ **Do not share personal information.**\n"
            "7️⃣ **Listen to staff and follow their instructions.**"
        ),
        "footer": "Thank you for keeping our server safe and enjoyable!"
    }
}

@bot.hybrid_command(name="rules", description="Display the official server rules")
@app_commands.guilds(discord.Object(id=GUILD_ID))
async def rules(ctx):
    locale = get_user_locale(ctx)
    t = RULES_TEXT[locale]

    embed = discord.Embed(
        title=t["title"],
        description=t["description"],
        color=0x5865F2
    )
    embed.add_field(name=t["field_name"], value=t["rules"], inline=False)
    embed.set_footer(text=t["footer"])

    await ctx.send(embed=embed)


@bot.event
async def on_member_join(member):

    channel = bot.get_channel(int(WELCOME_CHANNEL_ID))

    if channel is None:
        return

    embed = discord.Embed(
        description=f"Welcome {member.mention}!",
        color=0xFF73FA
    )

    embed.set_author(
        name=member.display_name,
        icon_url=member.display_avatar.url
    )

    embed.set_footer(text=f"User ID: {member.id}")

    await channel.send(embed=embed)     


bot.run(TOKEN)
import asyncio
import aiohttp
from aiogram import Bot, Dispatcher, types
from aiogram.filters import CommandStart
from config import BOT_TOKEN, CR_API_TOKEN

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

HEADERS = {
    "Authorization": f"Bearer {CR_API_TOKEN}"
}
PLAYER_API = "https://api.clashroyale.com/v1/players/%23{}"
CLAN_API = "https://api.clashroyale.com/v1/clans/%23{}"

async def api_get(url: str, max_retries: int = 5):
    """Запрос с прямым IP и ретраями"""
    for attempt in range(max_retries):
        try:
            timeout = aiohttp.ClientTimeout(
                total=30 + attempt * 10,
                connect=10 + attempt * 5
            )
            async with aiohttp.ClientSession(
                    headers=HEADERS,
                    timeout=timeout
            ) as session:
                async with session.get(url) as resp:
                    if resp.status == 200:
                        return await resp.json()
                    else:
                        print(f"Статус {resp.status}")
                        return None

        except asyncio.TimeoutError:
            print(f"⏱️ Таймаут, попытка {attempt + 1}/{max_retries}")
            await asyncio.sleep(3)

        except aiohttp.ClientConnectorDNSError:
            print(f"🌐 DNS ошибка, попытка {attempt + 1}/{max_retries}")
            await asyncio.sleep(3)

        except Exception as e:
            print(f"⚠️ Ошибка: {e}")
            await asyncio.sleep(2)

    return None


async def get_player(tag: str):
    tag = tag.replace("#", "").upper()
    return await api_get(PLAYER_API.format(tag))


async def get_clan(tag: str):
    tag = tag.replace("#", "").upper()
    return await api_get(CLAN_API.format(tag))


@dp.message(CommandStart())
async def start(message: types.Message):
    await message.answer(
        "🏆 <b>Clash Royale Stats Bot</b>\n\n"
        "Отправь <b>тег игрока</b> для получения статистики\n\n"
        "Пример: <code>#Y8V8P2R90</code>",
        parse_mode="HTML"
    )


@dp.message()
async def player_stats(message: types.Message):
    tag = message.text.strip()

    if not tag.startswith("#"):
        await message.answer("❌ Тег должен начинаться с #")
        return

    loading = await message.answer("⏳ Загрузка...")

    player = await get_player(tag)

    if not player:
        await loading.edit_text("⚠️ Игрок не найден или ошибка API")
        return

    text = (
        f"👑 <b>{player['name']}</b>\n"
        f"🆔 <code>{player['tag']}</code>\n\n"
        f"🏆 Трофеи: {player['trophies']}\n"
        f"🏅 Макс трофеи: {player['bestTrophies']}\n"
        f"🎮 Уровень: {player['expLevel']}\n\n"
        f"⚔️ Победы: {player['wins']}\n"
        f"💀 Поражения: {player['losses']}\n"
        f"📊 Боев: {player['battleCount']}\n\n"
    )

    if "currentFavouriteCard" in player:
        fav = player["currentFavouriteCard"]
        text += f"❤️ Любимая карта: <b>{fav['name']}</b>\n\n"

    if "currentDeck" in player:
        text += "🃏 <b>Текущая колода:</b>\n"
        for card in player["currentDeck"]:
            text += f"• {card['name']} (ур. {card['level']})\n"
        text += "\n"

    if "clan" in player:
        clan_tag = player["clan"]["tag"]
        clan = await get_clan(clan_tag)

        if clan:
            text += (
                f"👥 <b>Клан:</b> {clan['name']}\n"
                f"🏷 Тег: <code>{clan['tag']}</code>\n"
                f"👑 Игроков: {clan['members']}/50\n"
                f"🏆 Трофеи клана: {clan['clanScore']}\n"
                f"⚔️ Очки войны: {clan.get('clanWarTrophies', '—')}\n"
            )
    else:
        text += "👥 Клан: отсутствует\n"

    await loading.edit_text(text, parse_mode="HTML")


async def main():
    print("🚀 Запуск бота...")
    await bot.delete_webhook(drop_pending_updates=True)
    print("✅ Бот готов!")
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
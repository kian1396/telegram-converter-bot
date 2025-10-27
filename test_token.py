import asyncio
from telegram import Bot

TOKEN = "8254175129:AAFDAAiQL2ZfRYKYBOZPXNbt3UyHgOMzo_Y"

async def main():
    bot = Bot(token=TOKEN)
    info = await bot.get_me()
    print("✅ Bot is working! Name:", info.first_name)

asyncio.run(main())

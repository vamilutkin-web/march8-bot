import asyncio
import json
import os
from aiohttp import web
from pathlib import Path
from typing import Dict
from aiogram import Bot, Dispatcher, F
from aiogram.types import Message, ReplyKeyboardMarkup, KeyboardButton, FSInputFile
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.fsm.state import State, StatesGroup

import os
TOKEN = os.getenv("BOT_TOKEN")

ALLOW_REPEAT = True
MAX_ATTEMPTS = 3

DATA_DIR = Path("data")
MEDIA_DIR = Path("media")
DATA_DIR.mkdir(exist_ok=True)
MEDIA_DIR.mkdir(exist_ok=True)

DELIVERED_FILE = DATA_DIR / "delivered.json"
ATTEMPTS_FILE = DATA_DIR / "attempts.json"

GIFTS = {
    "Sexy Gangsterr": {
        "password": "11092005",
        "text": "Аня, поздравляю тебя с 8 марта.\n"
                "Оставайся такой же яркой, открытой, красивой и веселой. Не обращай внимание на других людей, твой характер отлично гармонирует с чувством стиля и прекрасным музыкальным вкусом. Не переживай по поводу несбывшихся ожиданий или резких перемен, все к лучшему.\n"
                "Сезон холода, скользких дорог и зимней депрессии подошёл к концу. Пусть этот праздник станет ознаменованием начала весны, самого прекрасного время года, предшествующего лету.\n\n"
                "Увидимся, HL",
        "image": MEDIA_DIR / "anya_k.jpg",
        "song": MEDIA_DIR / "anya_k.mp3",
        "song_title": "Именно Такой",
    },
    "Dead Blode": {
        "password": "22012007",
        "text": "Аня, прими мои поздравления с этим чудесным днем. Твоя утонченность, красота и скромность - качества, которые сейчас очень тяжело найти. С тобой всегда просто и легко, несмотря на всю неординарность личности.\n"
                "Надеюсь мистер крыс больше не будет воровать ваш майонез и пельмени, а наступившая весна порадует теплой погодой, хорошим настроением и интересными событиями.\n\n" 
                "Удачи, HL",
        "image": MEDIA_DIR / "anya_d.jpg",
        "song": MEDIA_DIR / "anya_d.mp3",
        "song_title": "Durch Den Monsun",
    },
    "Al_Gus": {
        "password": "26122006",
        "text": "Алена, наше добро и свет! Поздравляю с этим прекрасным праздником, оставайся всегда такой живой, пусть удача преследует тебя по пятам, а желания непременно сбываются.\n" 
                "Пусть время не изменит твоей открытости миру, продолжай радовать нас своей добротой, такие люди очень нужны на земле. Будь женственной и осозновай свой шарм!\n\n"
                "С праздником, S",
        "image": MEDIA_DIR / "alyona.jpg",
        "song": MEDIA_DIR / "alyona.mp3",
        "song_title": "Shape of My Heart",
    },
    "Zxacgh": {
        "password": "08082007",
        "text": "Мари, с 8 марта!\n"
                "Ты мое сокровище: твои зелёные глаза, твой взгляд, твой нежный аромат, то как ты думаешь и ведёшь себя... Все это невероятно.\n"
                "Я хочу, чтобы ты ощущала свою красоту так же сильно, как я её вижу, и чтобы счастье стало твоей постоянной спутницей… особенно рядом со мной\n"
                "Пусть тревоги уходят, а радость и любовь остаются. Ты заслуживаешь всего самого яркого в этом мире.\n\n"
                "Люблю, твой S",
        "image": MEDIA_DIR / "masha.jpg",
        "song": MEDIA_DIR / "masha.mp3",
        "song_title": "My Kind of Woman",
    },
}

class GiftStates(StatesGroup):
    CHOOSING_NAME = State()
    WAITING_PASSWORD = State()

def load_json(path: Path, default):
    if path.exists():
        return json.loads(path.read_text(encoding="utf-8"))
    return default

def save_json(path: Path, data):
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")

delivered: Dict[str, list] = load_json(DELIVERED_FILE, {})
attempts: Dict[str, dict] = load_json(ATTEMPTS_FILE, {})

names_kb = ReplyKeyboardMarkup(
    keyboard=[[KeyboardButton(text=name)] for name in GIFTS.keys()],
    resize_keyboard=True
)

bot = Bot(TOKEN)
storage = MemoryStorage()
dp = Dispatcher(storage=storage)

def normalize_pwd(raw: str) -> str:
    return "".join(ch for ch in raw if ch.isdigit())

@dp.message(CommandStart())
async def cmd_start(message: Message, state: FSMContext):
    await state.set_state(GiftStates.CHOOSING_NAME)
    await message.answer("Дорогие девушки, творческое объединение безработных программистов и писателей от всей души поздравляет вас с 8 марта. Чтобы получить секретное поздравление персонально, пожалуйста, выберете свое имя и введите код полученный ранее.\n\n"
    "С любовью HL и S", reply_markup=names_kb)

@dp.message(GiftStates.CHOOSING_NAME, F.text.in_(list(GIFTS.keys())))
async def choose_name(message: Message, state: FSMContext):
    name = message.text
    user_id = str(message.from_user.id)

    if not ALLOW_REPEAT and delivered.get(user_id) and name in delivered[user_id]:
        await message.answer("Вы уже получили поздравление 🎁", reply_markup=names_kb)
        return

    await state.update_data(chosen_name=name)

    attempts.setdefault(user_id, {})
    attempts[user_id][name] = 0
    save_json(ATTEMPTS_FILE, attempts)

    await state.set_state(GiftStates.WAITING_PASSWORD)
    await message.answer("Введите секретный код :3")

@dp.message(GiftStates.WAITING_PASSWORD)
async def check_password(message: Message, state: FSMContext):
    user_id = str(message.from_user.id)
    data = await state.get_data()
    name = data.get("chosen_name")

    if not name:
        await state.set_state(GiftStates.CHOOSING_NAME)
        await message.answer("Выберите имя 👇", reply_markup=names_kb)
        return

    entered = normalize_pwd(message.text)
    correct = GIFTS[name]["password"]

    attempts.setdefault(user_id, {})
    attempts[user_id].setdefault(name, 0)

    if entered == correct:
        delivered.setdefault(user_id, [])
        delivered[user_id].append(name)
        save_json(DELIVERED_FILE, delivered)

        gift = GIFTS[name]

        image_path = gift["image"]
        if image_path.exists():
            await bot.send_photo(
                chat_id=message.chat.id,
                photo=FSInputFile(image_path),
                caption=gift["text"]
    )
        else:
            await message.answer(gift["text"])
            await message.answer("Картинка не найдена (проверьте папку media).")

        await asyncio.sleep(5)
        
        song_path = gift.get("song")
        if song_path and song_path.exists():
            await bot.send_audio(
                chat_id=message.chat.id,
                audio=FSInputFile(song_path),
                title=gift.get("song_title"),
                caption="C праздником ❤"
     )
        await state.set_state(GiftStates.CHOOSING_NAME)
    else:
        attempts[user_id][name] += 1
        save_json(ATTEMPTS_FILE, attempts)

        if attempts[user_id][name] >= MAX_ATTEMPTS:
            await state.set_state(GiftStates.CHOOSING_NAME)
            await message.answer("Слишком много попыток. Возвращаем в меню.", reply_markup=names_kb)
        else:
            remain = MAX_ATTEMPTS - attempts[user_id][name]
            await message.answer(f"Неверный пароль. Осталось попыток: {remain}")
async def start_web_server():
    app = web.Application()

    async def health(request):
        return web.Response(text="ok")

    app.router.add_get("/", health)
    app.router.add_get("/health", health)

    runner = web.AppRunner(app)
    await runner.setup()

    port = int(os.environ.get("PORT", "10000"))
    site = web.TCPSite(runner, "0.0.0.0", port)
    print ("PORT env=", os.environ.get("PORT"))
    print("Starting web server on", port)
    await site.start()
async def main():
    await start_web_server()
    print("Бот запущен")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
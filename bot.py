import asyncio
import logging
import os
import json
import wave
import random
from aiogram import Bot, Dispatcher, F, Router
from aiogram.types import Message
from aiogram.filters import Command
from vosk import Model, KaldiRecognizer

# Настройка логирования
logging.basicConfig(level=logging.INFO)

# Токен бота. Рекомендуется установить его в переменную окружения TELEGRAM_BOT_TOKEN
TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "YOUR_TOKEN_HERE")

# Инициализация бота, диспетчера и маршрутизатора
bot = Bot(token=TOKEN)
dp = Dispatcher()
router = Router()

# Загрузка Vosk-модели. Папка "model" должна существовать и содержать модель.
MODEL_PATH = "model"
if not os.path.exists(MODEL_PATH):
    raise Exception("Модель Vosk не найдена! Скачайте и разместите её в папке 'model'.")
model = Model(MODEL_PATH)

# Обработчик команды /start
@router.message(Command("start"))
async def cmd_start(message: Message):
    await message.answer("Ahoj! Som slovenský jazykový bot. Pošli mi textovú alebo hlasovú správu.")

# Обработчик команды /question
@router.message(Command("question"))
async def cmd_question(message: Message):
    questions = [
        "Aké sú tvoje obľúbené koníčky?",
        "Čo si robil cez víkend?",
        "Aký je tvoj obľúbený film?",
    ]
    await message.answer(f"Tu je otázka pre teba: {random.choice(questions)}")

# Обработчик текстовых сообщений
@router.message(F.text)
async def text_handler(message: Message):
    await message.answer(f"Dostal som tvoju správu: {message.text}")

# Обработчик голосовых сообщений
@router.message(F.voice)
async def voice_handler(message: Message):
    # Скачиваем голосовое сообщение
    voice_file = await message.voice.download()  # возвращает file-like объект
    ogg_filename = "voice.ogg"
    with open(ogg_filename, "wb") as f:
        f.write(voice_file.getvalue())

    # Конвертируем OGG в WAV с помощью ffmpeg (убедись, что ffmpeg установлен)
    wav_filename = "voice.wav"
    os.system(f"ffmpeg -i {ogg_filename} -ar 16000 -ac 1 -c:a pcm_s16le {wav_filename}")

    # Распознаем голосовое сообщение с помощью Vosk
    wf = wave.open(wav_filename, "rb")
    rec = KaldiRecognizer(model, wf.getframerate())
    rec.SetWords(True)
    while True:
        data = wf.readframes(4000)
        if len(data) == 0:
            break
        rec.AcceptWaveform(data)
    result = json.loads(rec.FinalResult())
    recognized_text = result.get("text", "")
    if recognized_text:
        await message.answer(f"Rozpoznaný text: {recognized_text}")
    else:
        await message.answer("Prepáč, nerozpoznal som tvoju správu.")

    # Удаляем временные файлы
    os.remove(ogg_filename)
    os.remove(wav_filename)

# Главная функция для запуска бота
async def main():
    dp.include_router(router)  # Регистрируем маршрутизатор
    # Удаляем возможный вебхук и сбрасываем ожидающие обновления
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())

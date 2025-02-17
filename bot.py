import os
import logging
import asyncio
from aiogram import Bot, Dispatcher, types
from aiogram.types import Message
from aiogram.filters import Command
from aiogram.fsm.storage.memory import MemoryStorage
from vosk import Model, KaldiRecognizer
import wave
import json

# Включаем логирование
logging.basicConfig(level=logging.INFO)

# Загрузка API-токена из переменной окружения
TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")

# Инициализация бота и диспетчера
bot = Bot(token=TOKEN)
dp = Dispatcher(storage=MemoryStorage())

# Загрузка модели Vosk для распознавания речи
MODEL_PATH = "model"
if not os.path.exists(MODEL_PATH):
    raise Exception("Модель Vosk не найдена! Скачайте и разместите её в папке 'model'.")
model = Model(MODEL_PATH)

# Обработчик команды /start
@dp.message(Command("start"))
async def cmd_start(message: Message):
    await message.answer("Ahoj! Som Slovenský jazykový bot. Napíš mi správu alebo pošli hlasovú nahrávku.")

# Обработчик текстовых сообщений
@dp.message()
async def handle_text(message: Message):
    response = f"Dostal som tvoju správu: {message.text}"
    await message.answer(response)

# Обработчик голосовых сообщений
@dp.message(content_types=types.ContentType.VOICE)
async def handle_voice(message: Message):
    voice = await message.voice.download()
    file_path = "voice.ogg"
    with open(file_path, "wb") as f:
        f.write(voice.getvalue())
    
    # Конвертируем в WAV
    wav_path = "voice.wav"
    os.system(f"ffmpeg -i {file_path} -ar 16000 -ac 1 -c:a pcm_s16le {wav_path}")
    
    # Распознаем текст
    wf = wave.open(wav_path, "rb")
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
    
    # Удаляем файлы после обработки
    os.remove(file_path)
    os.remove(wav_path)

# Обработчик запроса вопроса
@dp.message(Command("question"))
async def cmd_question(message: Message):
    questions = [
        "Aké sú tvoje obľúbené koníčky?",
        "Čo si robil cez víkend?",
        "Aký je tvoj obľúbený film?",
    ]
    await message.answer(f"Tu je otázka pre teba: {random.choice(questions)}")

# Запуск бота
async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
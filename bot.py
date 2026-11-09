import asyncio
import logging
import os
from aiohttp import web
from aiogram import Bot, Dispatcher, F
from aiogram.filters import Command
from aiogram.types import Message, ReplyKeyboardMarkup, KeyboardButton
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext
from aiogram.fsm.storage.memory import MemoryStorage

# Token shu faylning o'zida (hosting muhitida BOT_TOKEN bo'lsa, o'sha ustun turadi)
TOKEN = os.getenv("BOT_TOKEN", "9018084439:AAFEikJyBMcPAbgLebjzAkE97wUXJG6Jkvs")

logging.basicConfig(level=logging.INFO)

bot = Bot(token=TOKEN)
dp = Dispatcher(storage=MemoryStorage())

# FSM holatlari (Bosqichlar)
class ScheduleState(StatesGroup):
    waiting_for_parallel = State()
    waiting_for_day = State()

# Haftaning kunlari ro'yxati
DAYS = [
    "1. Dushanba",
    "2. Seshanba",
    "3. Chorshanba",
    "4. Payshanba",
    "5. Juma",
    "6. Shanba"
]

# Darslarni raqamlab chiqarish uchun yordamchi funksiya
def format_lessons(lessons_list):
    if not lessons_list or lessons_list == ["Dars yo'q"]:
        return "🔹 Dars yo'q"
    result = ""
    for idx, lesson in enumerate(lessons_list, 1):
        result += f"{idx}- {lesson}\n"
    return result.strip()

# 1-11 sinflar uchun to'liq dars jadvallari (Urganch 6-maktab)
JADVAL = {
    # 1-sinflar
    "1-A": {
        "1. Dushanba": ["Kelajak soati", "Matematika", "Alifbe", "Tasviriy san'at", "Yozuv"],
        "2. Seshanba": ["Matematika", "Informatika", "Alifbe", "Tabiiy fan"],
        "3. Chorshanba": ["Matematika", "Alifbe", "Yozuv", "Musiqa"],
        "4. Payshanba": ["Matematika", "Alifbe", "Tasviriy san'at", "Tarbiya"],
        "5. Juma": ["Matematika", "Alifbe", "Yozuv", "Texnologiya", "Jismoniy tarbiya"],
        "6. Shanba": ["Dars yo'q"]
    },
    "1-B": {
        "1. Dushanba": ["Kelajak soati", "Matematika", "Alifbe", "Yozuv", "Ingliz tili"],
        "2. Seshanba": ["Matematika", "Tabiiy fan", "Alifbe", "Informatika"],
        "3. Chorshanba": ["Matematika", "Yozuv", "Musiqa", "Alifbe"],
        "4. Payshanba": ["Matematika", "Alifbe", "Yozuv", "Tarbiya"],
        "5. Juma": ["Matematika", "Texnologiya", "Yozuv", "Jismoniy tarbiya"],
        "6. Shanba": ["Dars yo'q"]
    },
    "1-D": {
        "1. Dushanba": ["Kelajak soati", "Matematika", "Musiqa", "Tabiiy fan", "Yozuv"],
        "2. Seshanba": ["Informatika", "Matematika", "Alifbe", "Yozuv"],
        "3. Chorshanba": ["Matematika", "Alifbe", "Tasviriy san'at", "Yozuv"],
        "4. Payshanba": ["Matematika", "Tarbiya", "Alifbe", "Ingliz tili"],
        "5. Juma": ["Matematika", "Alifbe", "Yozuv", "Texnologiya", "Jismoniy tarbiya"],
        "6. Shanba": ["Dars yo'q"]
    },
    
    # 2-sinflar
    "2-A": {
        "1. Dushanba": ["Kelajak soati", "Matematika", "Ingliz tili", "O'qish", "Musiqa"],
        "2. Seshanba": ["Ingliz tili", "Tarbiya", "Matematika", "Tabiiy fan"],
        "3. Chorshanba": ["Matematika", "Rus tili", "Ona tili", "Texnologiya"],
        "4. Payshanba": ["Matematika", "Ona tili", "Jismoniy tarbiya", "Tasviriy san'at"],
        "5. Juma": ["Matematika", "Ona tili", "Jismoniy tarbiya", "O'qish"],
        "6. Shanba": ["Dars yo'q"]
    },
    "2-B": {
        "1. Dushanba": ["Kelajak soati", "Ingliz tili", "Matematika", "Musiqa", "Ona tili"],
        "2. Seshanba": ["Matematika", "Ona tili", "O'qish", "Tarbiya"],
        "3. Chorshanba": ["Matematika", "Ona tili", "Rus tili", "O'qish", "Jismoniy tarbiya"],
        "4. Payshanba": ["Matematika", "Ona tili", "Tabiiy fan", "Rus tili", "Ingliz tili"],
        "5. Juma": ["Matematika", "O'qish", "Tasviriy san'at", "Jismoniy tarbiya", "Texnologiya"],
        "6. Shanba": ["Dars yo'q"]
    },
    "2-D": {
        "1. Dushanba": ["Kelajak soati", "Matematika", "Ona tili", "Jismoniy tarbiya", "O'qish"],
        "2. Seshanba": ["Matematika", "Ona tili", "Tarbiya", "Ingliz tili", "Texnologiya"],
        "3. Chorshanba": ["Matematika", "Ona tili", "Informatika", "Rus tili", "Jismoniy tarbiya"],
        "4. Payshanba": ["Matematika", "O'qish", "Musiqa", "Ingliz tili", "Rus tili"],
        "5. Juma": ["Matematika", "Ona tili", "O'qish", "Tasviriy san'at", "Tabiiy fan"],
        "6. Shanba": ["Dars yo'q"]
    },

    # 3-sinflar
    "3-A": {
        "1. Dushanba": ["Kelajak soati", "Matematika", "Ona tili", "Ingliz tili", "O'qish"],
        "2. Seshanba": ["Matematika", "Tabiiy fan", "Tasviriy san'at", "Tarbiya", "Ona tili"],
        "3. Chorshanba": ["Matematika", "Musiqa", "Texnologiya", "Jismoniy tarbiya", "O'qish"],
        "4. Payshanba": ["Ingliz tili", "Rus tili", "Matematika", "Ona tili", "O'qish"],
        "5. Juma": ["Informatika", "Matematika", "Jismoniy tarbiya", "Ona tili", "Rus tili"],
        "6. Shanba": ["Dars yo'q"]
    },
    "3-B": {
        "1. Dushanba": ["Kelajak soati", "Matematika", "Tasviriy san'at", "O'qish", "Ona tili"],
        "2. Seshanba": ["Matematika", "Informatika", "Tabiiy fan", "Ingliz tili", "Ona tili"],
        "3. Chorshanba": ["Matematika", "Musiqa", "Rus tili", "Ona tili", "Jismoniy tarbiya"],
        "4. Payshanba": ["Matematika", "Tarbiya", "Ona tili", "Ingliz tili", "O'qish"],
        "5. Juma": ["Rus tili", "Texnologiya", "Matematika", "O'qish", "Jismoniy tarbiya"],
        "6. Shanba": ["Dars yo'q"]
    },
    "3-D": {
        "1. Dushanba": ["Kelajak soati", "Matematika", "Ona tili", "Ingliz tili", "O'qish"],
        "2. Seshanba": ["Matematika", "Tabiiy fan", "Tasviriy san'at", "Tarbiya", "Ona tili"],
        "3. Chorshanba": ["Matematika", "Musiqa", "Texnologiya", "Jismoniy tarbiya", "O'qish"],
        "4. Payshanba": ["Ingliz tili", "Rus tili", "Matematika", "Ona tili", "O'qish"],
        "5. Juma": ["Informatika", "Matematika", "Jismoniy tarbiya", "Ona tili", "Rus tili"],
        "6. Shanba": ["Dars yo'q"]
    },

    # 4-sinflar
    "4-A": {
        "1. Dushanba": ["Kelajak soati", "Matematika", "Ona tili", "Texnologiya", "O'qish"],
        "2. Seshanba": ["Tarbiya", "Matematika", "Tabiiy fan", "Tasviriy san'at", "Jismoniy tarbiya"],
        "3. Chorshanba": ["Matematika", "O'qish", "Ingliz tili", "Ona tili", "Rus tili"],
        "4. Payshanba": ["Musiqa", "Ingliz tili", "Rus tili", "Matematika", "Informatika"],
        "5. Juma": ["Matematika", "Ona tili", "Jismoniy tarbiya", "O'qish", "Texnologiya"],
        "6. Shanba": ["Dars yo'q"]
    },
    "4-B": {
        "1. Dushanba": ["Kelajak soati", "Matematika", "Ingliz tili", "Ona tili", "Musiqa"],
        "2. Seshanba": ["Matematika", "Tabiiy fan", "Ingliz tili", "Ona tili", "Tasviriy san'at"],
        "3. Chorshanba": ["Matematika", "O'qish", "Informatika", "Jismoniy tarbiya", "Texnologiya"],
        "4. Payshanba": ["Rus tili", "Ona tili", "Tarbiya", "Matematika", "O'qish"],
        "5. Juma": ["Matematika", "Rus tili", "O'qish", "Jismoniy tarbiya", "Ona tili"],
        "6. Shanba": ["Dars yo'q"]
    },
    "4-D": {
        "1. Dushanba": ["Kelajak soati", "Ona tili", "Matematika", "Musiqa", "Tasviriy san'at"],
        "2. Seshanba": ["Matematika", "Ingliz tili", "O'qish", "Tabiiy fan", "Informatika"],
        "3. Chorshanba": ["Matematika", "Ona tili", "Jismoniy tarbiya", "Rus tili", "O'qish"],
        "4. Payshanba": ["Ingliz tili", "Rus tili", "Matematika", "Tarbiya", "Ona tili"],
        "5. Juma": ["Matematika", "Ona tili", "Jismoniy tarbiya", "O'qish", "Texnologiya"],
        "6. Shanba": ["Dars yo'q"]
    },

    # 5-sinflar (5-A shanba 5 soat qilindi)
    "5-A": {
        "1. Dushanba": ["Kelajak soati", "Ona tili", "Texnologiya", "Matematika", "Ingliz tili"],
        "2. Seshanba": ["Tasviriy san'at", "Ingliz tili", "Texnologiya", "Matematika", "Tarbiya"],
        "3. Chorshanba": ["Ona tili", "Ingliz tili", "Musiqa", "Matematika", "Tabiiy fan"],
        "4. Payshanba": ["Ona tili", "Jismoniy tarbiya", "Adabiyot", "Rus tili", "Ona tili"],
        "5. Juma": ["Texnologiya", "Tabiiy fan", "Matematika", "Adabiyot", "Jismoniy tarbiya"],
        "6. Shanba": ["Informatika", "Tarbiya", "Jismoniy tarbiya", "Matematika", "Adabiyot"]
    },
    "5-B": {
        "1. Dushanba": ["Kelajak soati", "Matematika", "Ona tili", "Adabiyot", "Jismoniy tarbiya", "Ingliz tili"],
        "2. Seshanba": ["Matematika", "Tabiiy fan", "Tarbiya", "Texnologiya", "Ingliz tili"],
        "3. Chorshanba": ["Matematika", "Ona tili", "Adabiyot", "Ingliz tili", "Texnologiya"],
        "4. Payshanba": ["Ona tili", "Tabiiy fan", "Rus tili"],
        "5. Juma": ["Matematika", "Ona tili", "Tarbiya", "Musiqa", "Jismoniy tarbiya"],
        "6. Shanba": ["Informatika", "Tarbiya"]
    },
    "5-D": {
        "1. Dushanba": ["Kelajak soati", "Musiqa", "Matematika", "Ingliz tili", "Ona tili", "Texnologiya"],
        "2. Seshanba": ["Tarbiya", "Matematika", "Informatika", "Tabiiy fan"],
        "3. Chorshanba": ["Rus tili", "Matematika", "Ingliz tili", "Ona tili", "Adabiyot"],
        "4. Payshanba": ["Tabiiy fan", "Ingliz tili", "Ona tili", "Jismoniy tarbiya"],
        "5. Juma": ["Tabiiy fan", "Matematika", "Texnologiya", "Jismoniy tarbiya"],
        "6. Shanba": ["Tarbiya", "Tabiiy fan"]
    },

    # 6-sinflar
    "6-A": {
        "1. Dushanba": ["Kelajak soati", "Ona tili", "Musiqa", "Texnologiya", "Matematika", "Jismoniy tarbiya"],
        "2. Seshanba": ["Ingliz tili", "Qadimgi dunyo tarixi", "Matematika", "Tabiiy fan", "Informatika", "Tarbiya"],
        "3. Chorshanba": ["Ona tili", "Rus tili", "Matematika", "Qadimgi dunyo tarixi", "Ingliz tili"],
        "4. Payshanba": ["Texnologiya", "Ona tili", "Tabiiy fan", "Adabiyot", "Ingliz tili"],
        "5. Juma": ["Matematika", "Rus tili", "Jismoniy tarbiya", "Tasviriy san'at", "Ingliz tili"],
        "6. Shanba": ["Tabiiy fan", "Musiqa", "Ona tili", "Matematika", "Adabiyot"]
    },
    "6-B": {
        "1. Dushanba": ["Kelajak soati", "Ingliz tili", "Ona tili", "Matematika", "Texnologiya"],
        "2. Seshanba": ["Texnologiya", "Tabiiy fan", "Tarix", "Matematika", "Tarbiya"],
        "3. Chorshanba": ["Ingliz tili", "Tarix", "Matematika", "Rus tili", "Tasviriy san'at"],
        "4. Payshanba": ["Ona tili", "Tarix", "Ingliz tili", "Jismoniy tarbiya", "Adabiyot"],
        "5. Juma": ["Matematika", "Rus tili", "Musiqa", "Informatika", "Jismoniy tarbiya"],
        "6. Shanba": ["Tabiiy fan", "Musiqa", "Ona tili", "Matematika", "Adabiyot"]
    },
    "6-D": {
        "1. Dushanba": ["Kelajak soati", "Ingliz tili", "Ona tili", "Matematika", "Texnologiya"],
        "2. Seshanba": ["Texnologiya", "Tabiiy fan", "Tarix", "Matematika", "Tarbiya"],
        "3. Chorshanba": ["Ingliz tili", "Tarix", "Matematika", "Rus tili", "Tasviriy san'at"],
        "4. Payshanba": ["Ona tili", "Tarix", "Ingliz tili", "Jismoniy tarbiya", "Adabiyot"],
        "5. Juma": ["Matematika", "Rus tili", "Musiqa", "Informatika", "Jismoniy tarbiya"],
        "6. Shanba": ["Tabiiy fan", "Musiqa", "Ona tili", "Matematika", "Adabiyot"]
    },

    # 7-sinflar
    "7-A": {
        "1. Dushanba": ["Kelajak soati", "Biologiya", "O'zbek tili", "Geografiya", "Kimyo", "Ingliz tili"],
        "2. Seshanba": ["O'zbek tili", "Informatika", "Tasviriy san'at", "Fizika", "Texnologiya", "Matematika"],
        "3. Chorshanba": ["Matematika", "Ona tili", "Ingliz tili", "Adabiyot", "Informatika", "Jismoniy tarbiya"],
        "4. Payshanba": ["O'zbek tili", "Fizika", "Tarbiya", "Geografiya", "Jismoniy tarbiya", "Texnologiya"],
        "5. Juma": ["Matematika", "Kimyo", "Rus tili", "Biologiya", "Musiqa"],
        "6. Shanba": ["Matematika", "Ingliz tili", "Adabiyot", "Geografiya", "O'qish", "Jahon tarixi"]
    },
    "7-B": {
        "1. Dushanba": ["Kelajak soati", "Matematika", "Kimyo", "Ona tili", "Ingliz tili", "Geografiya"],
        "2. Seshanba": ["Matematika", "Jahon tarixi", "Ingliz tili", "O'qish", "Fizika", "Texnologiya"],
        "3. Chorshanba": ["Matematika", "Ingliz tili", "Ona tili", "Informatika", "Jismoniy tarbiya", "Adabiyot"],
        "4. Payshanba": ["Tarbiya", "Musiqa", "Geografiya", "Fizika", "Texnologiya", "Jismoniy tarbiya"],
        "5. Juma": ["Kimyo", "Matematika", "Biologiya", "Rus tili", "O'qish", "Tasviriy san'at"],
        "6. Shanba": ["Ingliz tili", "Adabiyot", "Biologiya", "Rus tili", "O'qish", "Matematika"]
    },
    "7-D": {
        "1. Dushanba": ["Kelajak soati", "Ingliz tili", "Kimyo", "Matematika", "Ingliz tili", "Geografiya", "Ona tili"],
        "2. Seshanba": ["Ingliz tili", "Matematika", "Fizika", "Tarbiya", "O'qish", "Jismoniy tarbiya"],
        "3. Chorshanba": ["Ingliz tili", "Matematika", "Ona tili", "Texnologiya", "Informatika"],
        "4. Payshanba": ["Fizika", "O'qish", "Jismoniy tarbiya", "Texnologiya", "Geografiya", "Rus tili"],
        "5. Juma": ["Biologiya", "Ona tili", "Kimyo", "Matematika", "Rus tili", "Musiqa"],
        "6. Shanba": ["Biologiya", "Jahon tarixi", "Ingliz tili", "Matematika", "Rus tili", "Adabiyot"]
    },

    # 8-sinflar
    "8-A": {
        "1. Dushanba": ["Kelajak soati", "Algebra", "Ona tili", "Rus tili", "Ingliz tili"],
        "2. Seshanba": ["Algebra", "Geografiya", "O'qish", "Tarbiya", "Chizmachilik"],
        "3. Chorshanba": ["Algebra", "Ona tili", "Jismoniy tarbiya", "O'zbek tarixi", "Ingliz tili"],
        "4. Payshanba": ["O'zbek tili", "Jahon tarixi", "Rus tili", "Biologiya"],
        "5. Juma": ["Geometriya", "Informatika", "Kimyo", "Biologiya", "Jismoniy tarbiya"],
        "6. Shanba": ["Ona tili", "Geometriya", "Adabiyot", "Kimyo", "Fizika", "Ingliz tili"]
    },
    "8-B": {
        "1. Dushanba": ["Kelajak soati", "Algebra", "Rus tili", "Ona tili", "Informatika", "Texnologiya"],
        "2. Seshanba": ["Algebra", "Ingliz tili", "O'zbek tarixi", "Geografiya", "Tarbiya", "Chizmachilik"],
        "3. Chorshanba": ["Algebra", "Ingliz tili", "Ona tili", "O'zbek tarixi", "Ingliz tili", "Adabiyot"],
        "4. Payshanba": ["O'zbek tili", "Fizika", "Biologiya", "Rus tili", "Biologiya", "Jismoniy tarbiya"],
        "5. Juma": ["Jahon tarixi", "Fizika", "Chizmachilik", "Biologiya", "Kimyo", "Jismoniy tarbiya"],
        "6. Shanba": ["Geometriya", "Geografiya", "Biologiya", "Kimyo", "Adabiyot", "Ingliz tili"]
    },
    "8-D": {
        "1. Dushanba": ["Kelajak soati", "Algebra", "Geografiya", "Informatika", "Adabiyot", "Rus tili"],
        "2. Seshanba": ["Ingliz tili", "Chizmachilik", "Texnologiya", "O'zbek tarixi", "Algebra"],
        "3. Chorshanba": ["Ona tili", "Algebra", "O'zbek tili", "Tarbiya", "Rus tili"],
        "4. Payshanba": ["Ona tili", "Biologiya", "Jahon tarixi", "Jismoniy tarbiya", "Fizika", "Ingliz tili"],
        "5. Juma": ["Kimyo", "Ona tili", "Geometriya", "Jismoniy tarbiya", "Fizika"],
        "6. Shanba": ["Kimyo", "Biologiya", "Geometriya", "Informatika", "Adabiyot", "Geografiya"]
    },

    # 9-sinflar
    "9-A": {
        "1. Dushanba": ["Kelajak soati", "Ona tili", "Algebra", "Rus tili", "Adabiyot", "Ingliz tili"],
        "2. Seshanba": ["O'zbek tarixi", "Algebra", "Informatika", "Jismoniy tarbiya", "Geografiya"],
        "3. Chorshanba": ["Tarbiya", "Algebra", "Informatika", "Ingliz tili", "O'zbek tarixi", "Geografiya"],
        "4. Payshanba": ["Fizika", "Chizmachilik", "Ingliz tili", "Fizika", "Davlat va huquq", "Jahon tarixi"],
        "5. Juma": ["O'zbek tili", "Geometriya", "Jismoniy tarbiya", "Fizika", "Informatika", "Kimyo"],
        "6. Shanba": ["O'zbek tili", "Kimyo", "Geometriya", "Adabiyot", "Biologiya", "Fizika"]
    },
    "9-B": {
        "1. Dushanba": ["Kelajak soati", "Jismoniy tarbiya", "Algebra", "Ona tili", "Biologiya", "Adabiyot"],
        "2. Seshanba": ["Kimyo", "Algebra", "Ingliz tili", "Informatika", "O'zbek tarixi", "Geografiya"],
        "3. Chorshanba": ["Ingliz tili", "Rus tili", "Algebra", "Texnologiya", "Jismoniy tarbiya", "O'zbek tarixi"],
        "4. Payshanba": ["Kimyo", "Rus tili", "Ingliz tili", "Fizika", "Davlat va huquq", "Jahon tarixi"],
        "5. Juma": ["Chizmachilik", "Ona tili", "Geometriya", "Fizika", "Informatika", "Biologiya"],
        "6. Shanba": ["Geografiya", "Ona tili", "Adabiyot", "Geometriya", "Tarbiya"]
    },
    "9-D": {
        "1. Dushanba": ["Kelajak soati", "Ona tili", "Algebra", "Rus tili", "Adabiyot", "Ingliz tili"],
        "2. Seshanba": ["O'zbek tarixi", "Algebra", "Informatika", "Jismoniy tarbiya", "Geografiya"],
        "3. Chorshanba": ["Tarbiya", "Algebra", "Informatika", "Ingliz tili", "O'zbek tarixi", "Geografiya"],
        "4. Payshanba": ["Fizika", "Chizmachilik", "Ingliz tili", "Fizika", "Davlat va huquq", "Jahon tarixi"],
        "5. Juma": ["O'zbek tili", "Geometriya", "Jismoniy tarbiya", "Fizika", "Informatika", "Kimyo"],
        "6. Shanba": ["O'zbek tili", "Kimyo", "Geometriya", "Adabiyot", "Biologiya", "Fizika"]
    },

    # 10-sinflar
    "10-A": {
        "1. Dushanba": ["Kelajak soati", "Geografiya", "Biologiya", "Algebra", "Adabiyot", "CHQRT"],
        "2. Seshanba": ["Informatika", "Davlat va huquq", "Algebra", "Fizika", "Ingliz tili", "Kimyo"],
        "3. Chorshanba": ["Rus tili", "Informatika", "Algebra", "Ona tili", "Kimyo", "O'zbek tarixi"],
        "4. Payshanba": ["CHQRT", "Jahon tarixi", "Rus tili", "Jismoniy tarbiya"],
        "5. Juma": ["Adabiyot", "Jismoniy tarbiya", "Geometriya", "Biologiya", "Tarbiya", "Geografiya"],
        "6. Shanba": ["Fizika", "Ona tili", "Ingliz tili", "Geometriya"]
    },
    "10-B": {
        "1. Dushanba": ["Kelajak soati", "Ona tili", "Ingliz tili", "Algebra", "Rus tili", "Adabiyot", "CHQRT"],
        "2. Seshanba": ["Geografiya", "O'zbek tarixi", "Algebra", "Fizika", "Ingliz tili", "Kimyo"],
        "3. Chorshanba": ["CHQRT", "Algebra", "Informatika", "Adabiyot", "Ona tili"],
        "4. Payshanba": ["Rus tili", "Jahon tarixi", "Kimyo", "CHQRT", "Jismoniy tarbiya"],
        "5. Juma": ["Davlat va huquq", "Geometriya", "Geografiya", "Jismoniy tarbiya", "Biologiya"],
        "6. Shanba": ["Adabiyot", "Geometriya", "Fizika", "Biologiya", "Informatika"]
    },
    "10-D": {
        "1. Dushanba": ["Kelajak soati", "Ona tili", "Ingliz tili", "Algebra", "Rus tili", "Adabiyot", "CHQRT"],
        "2. Seshanba": ["Geografiya", "O'zbek tarixi", "Algebra", "Fizika", "Ingliz tili", "Kimyo"],
        "3. Chorshanba": ["CHQRT", "Algebra", "Informatika", "Adabiyot", "Ona tili"],
        "4. Payshanba": ["Rus tili", "Jahon tarixi", "Kimyo", "CHQRT", "Jismoniy tarbiya"],
        "5. Juma": ["Davlat va huquq", "Geometriya", "Geografiya", "Jismoniy tarbiya", "Biologiya"],
        "6. Shanba": ["Adabiyot", "Geometriya", "Fizika", "Biologiya", "Informatika"]
    },

    # 11-sinflar
    "11-A": {
        "1. Dushanba": ["Kelajak soati", "Astronomiya", "Ona tili", "Biologiya", "Jismoniy tarbiya", "Informatika"],
        "2. Seshanba": ["CHQRT", "Fizika", "Kimyo", "Algebra", "O'zbek tarixi", "Informatika"],
        "3. Chorshanba": ["Rus tili", "Ona tili", "Tarbiya", "Algebra", "CHQRT", "Informatika"],
        "4. Payshanba": ["Ingliz tili", "Kimyo", "Jismoniy tarbiya", "Jahon tarixi", "Adabiyot"],
        "5. Juma": ["Algebra", "Davlat va huquq", "Rus tili", "Geometriya"],
        "6. Shanba": ["Ingliz tili", "Adabiyot", "Tadbirkorlik asoslari", "Fizika", "Geometriya", "Biologiya"]
    },
    "11-B": {
        "1. Dushanba": ["Kelajak soati", "Biologiya", "Informatika", "Ona tili", "Algebra", "Jismoniy tarbiya"],
        "2. Seshanba": ["Fizika", "Ingliz tili", "CHQRT", "Algebra", "Kimyo", "O'zbek tarixi"],
        "3. Chorshanba": ["Informatika", "Tarbiya", "Adabiyot", "CHQRT"],
        "4. Payshanba": ["Jismoniy tarbiya", "Ingliz tili", "Ona tili", "Kimyo", "Rus tili"],
        "5. Juma": ["Fizika", "Biologiya", "Davlat va huquq", "Geometriya", "Rus tili"],
        "6. Shanba": ["Jahon tarixi", "Astronomiya", "Adabiyot", "Tadbirkorlik", "Algebra", "Geometriya"]
    },
    "11-D": {
        "1. Dushanba": ["Kelajak soati", "Astronomiya", "Ona tili", "Biologiya", "Jismoniy tarbiya", "Informatika"],
        "2. Seshanba": ["CHQRT", "Fizika", "Kimyo", "Algebra", "O'zbek tarixi", "Informatika"],
        "3. Chorshanba": ["Rus tili", "Ona tili", "Tarbiya", "Algebra", "CHQRT", "Informatika"],
        "4. Payshanba": ["Ingliz tili", "Kimyo", "Jismoniy tarbiya", "Jahon tarixi", "Adabiyot"],
        "5. Juma": ["Algebra", "Davlat va huquq", "Rus tili", "Geometriya"],
        "6. Shanba": ["Ingliz tili", "Adabiyot", "Tadbirkorlik asoslari", "Fizika", "Geometriya", "Biologiya"]
    }
}

# Asosiy sinflar menyusi (1-11)
main_keyboard = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="1-sinf"), KeyboardButton(text="2-sinf"), KeyboardButton(text="3-sinf")],
        [KeyboardButton(text="4-sinf"), KeyboardButton(text="5-sinf"), KeyboardButton(text="6-sinf")],
        [KeyboardButton(text="7-sinf"), KeyboardButton(text="8-sinf"), KeyboardButton(text="9-sinf")],
        [KeyboardButton(text="10-sinf"), KeyboardButton(text="11-sinf")]
    ],
    resize_keyboard=True
)

@dp.message(Command("start"))
async def start_cmd(message: Message, state: FSMContext):
    await state.clear()
    await message.answer(
        "Assalomu alaykum! Maktab dars jadvali botiga xush kelibsiz.\nQaysi sinf jadvali kerak?" \
        "\n\nRazzakov Boburbek tomonidan yaratilgan " 
        "\n@boburbekrazzakov",
        
        reply_markup=main_keyboard
    )

@dp.message(F.text.in_([f"{i}-sinf" for i in range(1, 12)]))
async def select_parallel(message: Message, state: FSMContext):
    sinf_raqami = message.text.split("-")[0]
    await state.update_data(grade=sinf_raqami)
    
    parallel_keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text=f"{sinf_raqami}-A"), KeyboardButton(text=f"{sinf_raqami}-B")],
            [KeyboardButton(text=f"{sinf_raqami}-D")],
            [KeyboardButton(text="🔙 Orqaga")]
        ],
        resize_keyboard=True
    )
    
    await state.set_state(ScheduleState.waiting_for_parallel)
    await message.answer(
        f"<b>{message.text}</b> uchun parallel sinfni tanlang:",
        reply_markup=parallel_keyboard,
        parse_mode="HTML"
    )

@dp.message(F.text == "🔙 Orqaga")
async def go_back(message: Message, state: FSMContext):
    current_state = await state.get_state()
    if current_state == ScheduleState.waiting_for_day.state:
        data = await state.get_data()
        grade = data.get("grade")
        parallel_keyboard = ReplyKeyboardMarkup(
            keyboard=[
                [KeyboardButton(text=f"{grade}-A"), KeyboardButton(text=f"{grade}-B")],
                [KeyboardButton(text=f"{grade}-D")],
                [KeyboardButton(text="🔙 Orqaga")]
            ],
            resize_keyboard=True
        )
        await state.set_state(ScheduleState.waiting_for_parallel)
        await message.answer("Parallel sinfni tanlang:", reply_markup=parallel_keyboard)
    else:
        await state.clear()
        await message.answer("Asosiy menyu:", reply_markup=main_keyboard)

@dp.message(ScheduleState.waiting_for_parallel, F.text.regexp(r"^\d{1,2}-[A-D]$"))
async def select_day(message: Message, state: FSMContext):
    selected_class = message.text
    await state.update_data(class_name=selected_class)
    
    day_keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text=DAYS[0]), KeyboardButton(text=DAYS[1])],
            [KeyboardButton(text=DAYS[2]), KeyboardButton(text=DAYS[3])],
            [KeyboardButton(text=DAYS[4]), KeyboardButton(text=DAYS[5])],
            [KeyboardButton(text="🔙 Orqaga")]
        ],
        resize_keyboard=True
    )
    
    await state.set_state(ScheduleState.waiting_for_day)
    await message.answer(
        f"<b>{selected_class}</b> sinfi uchun haftaning qaysi kuni kerak?",
        reply_markup=day_keyboard,
        parse_mode="HTML"
    )

@dp.message(ScheduleState.waiting_for_day, F.text.in_(DAYS))
async def show_schedule(message: Message, state: FSMContext):
    data = await state.get_data()
    class_name = data.get("class_name")
    selected_day = message.text
    
    class_schedule = JADVAL.get(class_name, {})
    day_lessons = class_schedule.get(selected_day, ["Dars yo'q"])
    formatted_lessons = format_lessons(day_lessons)
    
    response_text = (
        f"📅 <b>{class_name} sinf dars jadvali</b>\n"
        f"📌 <b>Kun:</b> {selected_day}\n\n"
        f"{formatted_lessons}"
    )
    
    day_keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text=DAYS[0]), KeyboardButton(text=DAYS[1])],
            [KeyboardButton(text=DAYS[2]), KeyboardButton(text=DAYS[3])],
            [KeyboardButton(text=DAYS[4]), KeyboardButton(text=DAYS[5])],
            [KeyboardButton(text="🔙 Orqaga")]
        ],
        resize_keyboard=True
    )
    
    await message.answer(response_text, parse_mode="HTML", reply_markup=day_keyboard)

# Render (Web Service) kabi hostinglar port ochilishini talab qiladi.
# Shu uchun kichik "health check" server ishga tushiriladi.
async def health(request):
    return web.Response(text="Bot ishlayapti")

async def start_web_server():
    app = web.Application()
    app.router.add_get("/", health)
    runner = web.AppRunner(app)
    await runner.setup()
    port = int(os.getenv("PORT", "8080"))
    site = web.TCPSite(runner, "0.0.0.0", port)
    await site.start()
    logging.info(f"Web server {port}-portda ishga tushdi")

async def main():
    await start_web_server()
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
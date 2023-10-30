import asyncio
import utils
import logging
import sys
import text
from db import Database
from aiogram.filters import CommandStart, Command
from aiogram.types import Message, KeyboardButton, ReplyKeyboardMarkup, ReplyKeyboardRemove
from config import BOT_TOKEN
from aiogram import Dispatcher, Bot
from aiogram.enums import ParseMode
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage


TOKEN = BOT_TOKEN
storage = MemoryStorage()
dp = Dispatcher(storage=storage)
db = Database()


class UserRegistration(StatesGroup):
    user_name = State()


class AddRecord(StatesGroup):
    date = State()
    location = State()
    description = State()
    photos = State()


@dp.message(CommandStart())
async def start_handler(message: Message):
    user_name = db.get_user(user_id=message.from_user.id)
    if user_name:
        kb_start = ReplyKeyboardMarkup(resize_keyboard=True,
                                       keyboard=[[KeyboardButton(text="Додати запис")],
                                                 [KeyboardButton(text="Подивитись історію записів")]])
        await message.answer(text=f"Привіт рибацюга {user_name}. Цей бот - зручним помічником рибака, "
                                  f"в нього можна зберегти запис з рибалки, а потім зручно його достати!",
                             reply_markup=kb_start)
        kb_start.keyboard.clear()
    else:
        kb_reg = ReplyKeyboardMarkup(resize_keyboard=True, keyboard=[[KeyboardButton(text="Реєстрація")]])
        await message.answer(text="Будь ласка, зареєструйтесь", reply_markup=kb_reg)
        kb_reg.keyboard.clear()


@dp.message(lambda message: message.text == "Реєстрація")
async def start_registration(message: Message, state: FSMContext):
    await state.set_state(UserRegistration.user_name)
    await message.answer(text="Введіть будь ласка ім'я та фамілію!", reply_markup=ReplyKeyboardRemove())


@dp.message(UserRegistration.user_name)
async def end_registration(message: Message, state: FSMContext):
    db.reg_user(user_name=message.text, user_id=message.from_user.id)
    await message.answer(text="Реєстрація, пройшла успішно! Для того щоб подивитись функціонал бота натисніть - /help")
    await state.clear()


@dp.message(Command('help'))
async def help_command(message: Message, state: FSMContext):
    user_name = db.get_user(user_id=message.from_user.id)
    if user_name:
        await message.answer(text=text.HELP_COMMAND)
    else:
        await message.answer(text="Ви не зареєстровані!")
        await start_registration(message, state)


@dp.message(lambda message: message.text == "Додати запис")
async def start_adding_record(message: Message, state: FSMContext):
    await state.set_state(AddRecord.date)
    kb_date = ReplyKeyboardMarkup(resize_keyboard=True, keyboard=[[KeyboardButton(text="Відправити дату")]])
    await message.answer(text="Ну що ж почнемо, для початку відправте дату!", reply_markup=kb_date)


@dp.message(lambda message: message.text == "Відправити дату" and AddRecord.date)
async def send_location(message: Message, state: FSMContext):
    await state.update_data(date=utils.send_date())
    await state.set_state(AddRecord.location)
    kb_location = ReplyKeyboardMarkup(resize_keyboard=True, keyboard=[[KeyboardButton(text="Відправити автоматично")],
                                                                      [KeyboardButton(text="Записати самому")]])
    await message.answer(text="Відправте геолокацію автоматично або ж запишіть де ви знаходитесь!",
                         reply_markup=kb_location)


async def main() -> None:
    bot = Bot(token=TOKEN, parse_mode=ParseMode.HTML)
    await dp.start_polling(bot)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, stream=sys.stdout)
    asyncio.run(main())

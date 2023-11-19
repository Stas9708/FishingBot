import asyncio
import datetime
import logging
import sys
from aiogram import Dispatcher, Bot, F
from aiogram.enums import ParseMode
from aiogram.filters import CommandStart, Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import Message, KeyboardButton, ReplyKeyboardMarkup, ReplyKeyboardRemove

import text
import utils
from config import BOT_TOKEN
from db import Database


TOKEN = BOT_TOKEN
bot = Bot(TOKEN)
dp = Dispatcher()
db = Database()


class UserRegistration(StatesGroup):
    user_name = State()


class AddRecord(StatesGroup):
    date = State()
    location = State()
    weather = State()
    description = State()
    photos = State()


@dp.message(CommandStart())
async def start_handler(message: Message):
    user_name = db.get_user_info(user_id=message.from_user.id)['user_name']
    if user_name:
        kb_start = ReplyKeyboardMarkup(resize_keyboard=True,
                                       keyboard=[[KeyboardButton(text="Додати запис")],
                                                 [KeyboardButton(text="Подивитись історію записів")]])
        await message.answer(text=f"Привіт рибацюга {user_name}. Цей бот є зручним помічником рибака, "
                                  f"в нього можна зберегти запис з рибалки, а потім зручно його достати!",
                             reply_markup=kb_start)
        kb_start.keyboard.clear()
    else:
        kb_reg = ReplyKeyboardMarkup(resize_keyboard=True, keyboard=[[KeyboardButton(text="Реєстрація")]])
        await message.answer(text="Будь ласка, зареєструйтесь", reply_markup=kb_reg)
        kb_reg.keyboard.clear()


@dp.message(F.text == "Реєстрація")
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
    user_name = db.get_user_info(user_id=message.from_user.id)['user_name']
    if user_name:
        await message.answer(text=text.HELP_COMMAND)
    else:
        await message.answer(text="Ви не зареєстровані!")
        await start_registration(message, state)


@dp.message(F.text == "Додати запис")
async def start_adding_record(message: Message, state: FSMContext):
    await state.set_state(AddRecord.date)
    kb_date = ReplyKeyboardMarkup(resize_keyboard=True, keyboard=[[KeyboardButton(text="Відправити дату")]])
    await message.answer(text="Ну що ж почнемо, для початку відправте дату!", reply_markup=kb_date)


@dp.message(F.text == "Відправити дату" and AddRecord.date)
async def send_location(message: Message, state: FSMContext):
    await state.update_data(date=datetime.datetime.now().strftime("%d-%m-%Y"))
    await state.set_state(AddRecord.location)
    kb_location = ReplyKeyboardMarkup(resize_keyboard=True, keyboard=[[KeyboardButton(text="Відправити геолокацію",
                                                                                      request_location=True)]])
    await message.answer(text="Відправте геолокацію!",
                         reply_markup=kb_location)


@dp.message(lambda message: message.location)
async def send_location_automatically(message: Message, state: FSMContext):
    await state.set_state(AddRecord.location)
    await state.update_data(location={"lat": message.location.latitude,
                                      "lon": message.location.longitude})
    kb_weather = ReplyKeyboardMarkup(resize_keyboard=True, keyboard=[[KeyboardButton(text="Відправити дані погоди")]])
    await message.answer(text="І куди ж без такої важливої частини як погода, добре що в мене все автоматично.",
                         reply_markup=kb_weather)


@dp.message(F.text == "Відправити дані погоди")
async def send_weather_automatically(message: Message, state: FSMContext):
    await state.set_state(AddRecord.weather)
    data = await state.get_data()
    location = data.get('location')
    weather = await utils.weather_info_parser(await utils.send_weather(location['lat'], location['lon']))
    await state.update_data(weather=weather)
    await message.answer(text="Тепер напишіть те, що ви хотіли б запамʼятати з даної риболовної сесії:\n"
                              "-яка насадка краще працювала\n"
                              "-який корм краще працював (виробник, колір, смак і т.д.)\n"
                              "-довжина та діаметр повідця\n"
                              "-розмір гачка (виробник, колір і т.д.)\n"
                              "-яка була дистація ловлі\n"
                              "Тобто ваше завдання, записати все що допоможе вам в наступних риболовлях на цьому місці."
                         , reply_markup=ReplyKeyboardRemove())


@dp.message(AddRecord.weather)
async def send_photo(message: Message, state: FSMContext):
    await state.set_state(AddRecord.description)
    await state.update_data(description=message.text)
    await message.answer(text="Ми майже закінчили, залишилось відправити фотографії улову, які допоможуть вам згадати "
                              "що ви зловили на цій риболовлі!\nВи можете відправити альбом, в якому знаходиться не "
                              "більше 5 фотографій!")


@dp.message(AddRecord.description and F.photo)
async def end_record(message: Message, state: FSMContext):
    await state.set_state(AddRecord.photos)
    data = await state.get_data()
    if message.media_group_id not in utils.photo_count_per_user:
        utils.photo_count_per_user[message.media_group_id] = 1
    else:
        if utils.photo_count_per_user[message.media_group_id] > 5:
            await message.answer(text="Ви надіслали забагато фото, максимальна дозволена кількість 5!\n"
                                      "Давайте ще раз.")
            await send_photo(message, state)
        else:
            utils.photo_count_per_user[message.media_group_id] += 1
    db.add_record_to_table(db.get_user_info(message.from_user.id)['id'], data['date'], data['location'],
                           data['description'], message.photo[-1].file_id, data['weather'], message.media_group_id)


async def main() -> None:
    bot_1 = Bot(token=TOKEN, parse_mode=ParseMode.HTML)
    await dp.start_polling(bot_1)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, stream=sys.stdout)
    asyncio.run(main())

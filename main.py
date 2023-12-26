import asyncio
from datetime import timedelta

import aiogram
from aiogram.utils import exceptions
from aiogram import Bot, Dispatcher, types, executor
from aiogram.utils.exceptions import MessageNotModified

from config import TOKEN_API

from keyboard import main_kb, b_context_menu, b_yes_or_no, kb_back, b_Up_Dn, kb_update, kb_examination_ok, \
    kb_for_settings, b_search_type, b_editing_switches

from sqlite import db_start, upload_data_to_db, get_ids, get_profile, delete_table_row, \
    download_all_data_for_examination, upload_data_to_examination, get_examination_data, get_workers_data, \
    workers_switches, upload_data_to_workers

from extract_id import extract_id, extract_name

from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters import Text
from aiogram.dispatcher.filters.state import StatesGroup, State
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher import filters
from datetime import date
from datetime import datetime
import re
from time_until import time_until, seconds_to_dhms, parse_time
from search_word import search_word_in_text

users = {}
workers = {}
boards = {}
storage = MemoryStorage()
bot = Bot(TOKEN_API)
dp = Dispatcher(bot=bot,
                storage=storage)


async def on_startup(_):
    await db_start()


class User:
    def __init__(self, user_id, chat_id, mess_id=None, mess_id2=None, start_mess_id=0, profile_id=0, temp_mess_id=0,
                 date_switches='', hours='', minutes='', profile_id_for_worker=0, day=0, search_data='',
                 editing_switches=0):
        self.start_mess_id = start_mess_id

        self.user_id = user_id
        self.chat_id = chat_id

        if mess_id is None:
            mess_id = []
        self.mess_id = mess_id

        if mess_id2 is None:
            mess_id2 = []
        self.mess_id2 = mess_id2

        self.profile_id = profile_id
        self.profile_id_for_worker = profile_id_for_worker

        self.temp_mess_id = temp_mess_id

        self.date_switches = date_switches
        self.editing_switches = editing_switches

        self.hours = hours
        self.minutes = minutes
        self.day = day

        self.search_data = search_data


class Worker:
    def __init__(self, chat_id, profile_id, workers_name, every_day=False):
        self.chat_id = chat_id
        self.profile_id = profile_id
        self.workers_name = workers_name

        self.every_day = every_day

    async def dynamic_message(self, wait_for, profile_id, user_id):

        while True:
            await asyncio.sleep(wait_for)

            sent_mess = await bot.send_message(chat_id=self.chat_id,
                                               text=(f"<pre>Час обстеження: \n</pre>"
                                                     f"<pre>{await get_profile(profile_id)}</pre>"),
                                               parse_mode="HTML",
                                               reply_markup=kb_examination_ok)
            users[user_id].mess_id.append(sent_mess.message_id)

            every_day = await get_examination_data(profile_id)

            if every_day[4] == '1':
                date = await get_examination_data(profile_id)
                date = await parse_time(date[3])
                date['day'] = int(date['day']) + 1
                await upload_data_to_examination(f"{date['hours']}:{date['minutes']} - {date['day']}",
                                                 'scheduling_time',
                                                 self.profile_id)
                wait_for = await time_until(date['hours'], date['minutes'], date['day'])
            else:
                await upload_data_to_examination("Не заплановано", "scheduling_time", profile_id)
                break


class PlanningBoard:
    def __init__(self, user_id):
        self.user_id = user_id

    static_planning_board = f"<pre>Тут будуть з'являтися заплановані обстеження\n</pre>"

    async def update_board(self, chat_id, message_id):
        ids = await get_ids()
        info = f"<pre>Тут будуть з'являтися заплановані обстеження\n</pre>"

        for id in ids:
            worker = await get_workers_data(id[0])
            examination_data = await get_examination_data(id[0])
            if examination_data[3] != 'Не заплановано':
                info += f"{worker[2]} - {examination_data[3]}\n"

        self.static_planning_board = info

        try:
            await bot.edit_message_text(chat_id=chat_id,
                                        message_id=message_id,
                                        text=self.static_planning_board,
                                        parse_mode='HTML',
                                        reply_markup=kb_update)
        except MessageNotModified as e:
            return f"Нових запланувань не знайдено"


class ProfileStatesGroup(StatesGroup):
    registration_date = State()
    name = State()
    phone_num = State()

    photo = State()

    examination_res = State()
    examination_date = State()
    examination_time = State()
    # examination_planning = State()

    search_worker = State()

    editing = State()
    set_data = State()


@dp.message_handler(commands=['start'])
async def cmd_start(message: types.Message):
    user_id = message.from_user.id

    if user_id not in users:
        users[user_id] = User(user_id, chat_id=message.chat.id)
        boards[user_id] = PlanningBoard(user_id)

    print(message)

    await message.delete()
    sent_mess = await message.answer("Вітаю!", reply_markup=main_kb)
    board = await bot.send_message(chat_id=message.chat.id,
                                   text=boards[user_id].static_planning_board,
                                   reply_markup=kb_update,
                                   parse_mode="HTML")
    await boards[user_id].update_board(message.chat.id, board.message_id)

    users[user_id].start_mess_id = sent_mess.message_id


@dp.callback_query_handler(lambda callback_query: callback_query.data.startswith('examination_ok'))
async def delete_reminder(callback: types.CallbackQuery):
    await bot.delete_message(callback.message.chat.id, callback.message.message_id)


@dp.callback_query_handler(lambda callback_query: callback_query.data.startswith('update'))
async def board_update(callback: types.CallbackQuery):
    board = boards[callback.from_user.id]

    if callback.data == 'update':
        res = await board.update_board(callback.message.chat.id, callback.message.message_id)
        if res:
            await callback.answer(res)


@dp.message_handler(state=ProfileStatesGroup.examination_res)
async def load_examination_res(message: types.Message, state: FSMContext):
    user = users[message.from_user.id]
    user.mess_id2.append(message.message_id)

    async with state.proxy() as data:
        data['examination_date'] = date.today()
        data['examination_res'] = message.text

    await download_all_data_for_examination(state, user.profile_id)

    await bot.edit_message_text(chat_id=message.chat.id,
                                message_id=user.temp_mess_id,
                                text=await get_profile(user.profile_id),
                                parse_mode="HTML",
                                reply_markup=b_context_menu)

    sent_mess = await bot.send_message(chat_id=message.chat.id,
                                       text="Готов!")
    user.mess_id2.append(sent_mess.message_id)

    await asyncio.sleep(2)

    user.mess_id2 = await clear(user.mess_id2, message.chat.id)

    await state.finish()


@dp.message_handler(state=ProfileStatesGroup.examination_time)
async def load_examination_time(message: types.Message):
    user = users[message.from_user.id]
    user.mess_id2.append(message.message_id)

    if user.date_switches == 'hours':
        user.hours = message.text
        await bot.edit_message_text(chat_id=message.chat.id,
                                    message_id=user.temp_mess_id,
                                    text=f"Вкажіть час обстеження - <u>{user.hours}</u>:{user.minutes} - {user.day}",
                                    reply_markup=b_Up_Dn,
                                    parse_mode="HTML")

    if user.date_switches == 'minutes':
        user.minutes = message.text
        await bot.edit_message_text(chat_id=message.chat.id,
                                    message_id=user.temp_mess_id,
                                    text=f"Вкажіть час обстеження - {user.hours}:<u>{user.minutes}</u> - {user.day}",
                                    reply_markup=b_Up_Dn,
                                    parse_mode="HTML")

    if user.date_switches == 'day':
        user.day = message.text
        await bot.edit_message_text(chat_id=message.chat.id,
                                    message_id=user.temp_mess_id,
                                    text=f"Вкажіть час обстеження - {user.hours}:{user.minutes} - <u>{user.day}</u> ",
                                    reply_markup=b_Up_Dn,
                                    parse_mode="HTML")


@dp.callback_query_handler(lambda callback_query: callback_query.data.startswith('Pg'),
                           state=ProfileStatesGroup.examination_time)
async def date_switches(callback: types.CallbackQuery, state: FSMContext):
    user = users[callback.from_user.id]
    worker = workers[user.profile_id_for_worker]

    if callback.data == 'Pg_hours':
        try:
            await bot.edit_message_text(chat_id=callback.message.chat.id,
                                        message_id=callback.message.message_id,
                                        text=f"Вкажіть час обстеження - <u>{user.hours}</u>:{user.minutes} - {user.day}",
                                        reply_markup=b_Up_Dn,
                                        parse_mode="HTML")
            user.date_switches = 'hours'
        except MessageNotModified as e:
            await callback.answer(text="Години")

    if callback.data == 'Pg_minutes':
        try:
            await bot.edit_message_text(chat_id=callback.message.chat.id,
                                        message_id=callback.message.message_id,
                                        text=f"Вкажіть час обстеження - {user.hours}:<u>{user.minutes}</u> - {user.day}",
                                        reply_markup=b_Up_Dn,
                                        parse_mode="HTML")
            user.date_switches = 'minutes'
        except MessageNotModified as e:
            await callback.answer(text="Хвилини")

    if callback.data == 'Pg_day':
        try:
            await bot.edit_message_text(chat_id=callback.message.chat.id,
                                        message_id=callback.message.message_id,
                                        text=f"Вкажіть час обстеження - {user.hours}:{user.minutes} - <u>{user.day}</u>",
                                        reply_markup=b_Up_Dn,
                                        parse_mode="HTML")
            user.date_switches = 'day'
        except MessageNotModified as e:
            await callback.answer(text="День")

    if callback.data == 'Pg_ok':
        asyncio.create_task(
            worker.dynamic_message(await time_until(user.hours, user.minutes, user.day), worker.profile_id,
                                   callback.from_user.id))

        await upload_data_to_examination(f"{user.hours}:{user.minutes} - {user.day}", 'scheduling_time',
                                         worker.profile_id)

        await callback.answer(text="Обстеження заплановано")

        await bot.edit_message_text(chat_id=callback.message.chat.id,
                                    message_id=callback.message.message_id,
                                    text=await get_profile(worker.profile_id),
                                    parse_mode='HTML',
                                    reply_markup=b_context_menu)

        await clear(user.mess_id2, callback.message.chat.id)
        await state.finish()

    if callback.data == 'Pg_back':
        await bot.edit_message_text(chat_id=callback.message.chat.id,
                                    message_id=callback.message.message_id,
                                    text=await get_profile(worker.profile_id),
                                    parse_mode='HTML',
                                    reply_markup=b_context_menu)

        await state.finish()


@dp.message_handler(state=ProfileStatesGroup.set_data)
async def load_examination_res(message: types.Message, state: FSMContext):
    user = users[message.from_user.id]
    if user.editing_switches == 1:
        await upload_data_to_workers(message.text, 'name', user.profile_id)
        sent_mess = await bot.edit_message_text(chat_id=message.chat.id,
                                                message_id=user.temp_mess_id,
                                                text=await get_profile(user.profile_id),
                                                reply_markup=b_context_menu,
                                                parse_mode="HTML")
    if user.editing_switches == 2:
        await upload_data_to_workers(message.text, 'phone_num', user.profile_id)
        sent_mess = await bot.edit_message_text(chat_id=message.chat.id,
                                                message_id=user.temp_mess_id,
                                                text=await get_profile(user.profile_id),
                                                reply_markup=b_context_menu,
                                                parse_mode="HTML")
    await state.finish()


@dp.callback_query_handler(lambda callback_query: callback_query.data.startswith('Pg'),
                           state=ProfileStatesGroup.editing)
async def date_switches(callback: types.CallbackQuery, state: FSMContext):
    user = users[callback.from_user.id]

    if callback.data == "Pg_up" and user.editing_switches != 1:
        user.editing_switches -= 1
        sent_mess = await bot.edit_message_text(chat_id=callback.message.chat.id,
                                                message_id=callback.message.message_id,
                                                text=await workers_switches(user.editing_switches,
                                                                            await extract_id(callback.message.text)),
                                                reply_markup=b_editing_switches,
                                                parse_mode="HTML")

    if callback.data == "Pg_dn" and user.editing_switches != 2:
        user.editing_switches += 1
        sent_mess = await bot.edit_message_text(chat_id=callback.message.chat.id,
                                                message_id=callback.message.message_id,
                                                text=await workers_switches(user.editing_switches,
                                                                            await extract_id(callback.message.text)),
                                                reply_markup=b_editing_switches,
                                                parse_mode="HTML")

    if callback.data == "Pg_ok":
        user.temp_mess_id = callback.message.message_id
        user.profile_id = await extract_id(callback.message.text)
        if user.editing_switches == 1:
            sent_mess = await bot.send_message(chat_id=callback.message.chat.id,
                                               text=f"Надайте нове ім'я",
                                               parse_mode="HTML", )
        if user.editing_switches == 2:
            sent_mess = await bot.send_message(chat_id=callback.message.chat.id,
                                               text=f"Надайте новий номер телефону",
                                               parse_mode="HTML", )
        await ProfileStatesGroup.set_data.set()


@dp.callback_query_handler(lambda callback_query: callback_query.data.startswith('menu'))
async def context_menu(callback: types.CallbackQuery):
    user = users[callback.from_user.id]

    if callback.data == 'menu_delete' or callback.data == 'menu_no' or callback.data == 'menu_yes':
        if callback.data == 'menu_delete':
            await bot.edit_message_text(chat_id=callback.message.chat.id,
                                        message_id=callback.message.message_id,
                                        text=await get_profile(await extract_id(callback.message.text)),
                                        parse_mode='HTML',
                                        reply_markup=b_yes_or_no)

        if callback.data == 'menu_yes':
            await delete_table_row(await extract_id(callback.message.text))
            await bot.delete_message(chat_id=callback.message.chat.id,
                                     message_id=callback.message.message_id)

        elif callback.data == 'menu_no':
            await bot.edit_message_text(chat_id=callback.message.chat.id,
                                        message_id=callback.message.message_id,
                                        text=await get_profile(await extract_id(callback.message.text)),
                                        parse_mode='HTML',
                                        reply_markup=b_context_menu)

    if callback.data == 'menu_add_examination_res':
        user.profile_id = await extract_id(callback.message.text)
        user.temp_mess_id = callback.message.message_id

        sent_mess = await bot.send_message(chat_id=callback.message.chat.id,
                                           text="Надайте опис обстеження")
        user.mess_id2.append(sent_mess.message_id)

        await ProfileStatesGroup.examination_res.set()

    if callback.data == 'menu_schedule_an_examination':
        # Додаємо(створюємо) об'єкти класа Worker в список workers
        profile_id = await extract_id(callback.message.text)
        workers_name = await extract_name(callback.message.text)
        if profile_id not in workers:
            workers[profile_id] = Worker(callback.message.chat.id, profile_id, workers_name)

        today = datetime.today()
        time_now = datetime.now()

        user.profile_id_for_worker = profile_id
        user.date_switches = 'hours'
        user.hours = time_now.strftime('%H')
        user.minutes = time_now.strftime('%M')
        user.day = today.strftime('%d')

        sent_mess = await bot.edit_message_text(chat_id=callback.message.chat.id,
                                                message_id=callback.message.message_id,
                                                text=f"Вкажіть час обстеження - <u>{user.hours}</u>:{user.minutes} - {user.day}",
                                                reply_markup=b_Up_Dn,
                                                parse_mode="HTML")
        user.temp_mess_id = sent_mess.message_id

        await ProfileStatesGroup.examination_time.set()

    if callback.data == "menu_settings":
        profile_id = await extract_id(callback.message.text)
        user_id = callback.from_user.id
        if user_id not in users:
            users[user_id] = User(user_id, chat_id=callback.message.chat.id)
        if profile_id not in workers:
            workers[profile_id] = Worker(callback.message.chat.id, profile_id,
                                         await extract_name(callback.message.text))
        worker = workers[await extract_id(callback.message.text)]
        users[user_id].profile_id_for_worker = profile_id

        every_day = await get_examination_data(worker.profile_id)
        if every_day[4] == '0':
            await bot.edit_message_text(chat_id=callback.message.chat.id,
                                        message_id=callback.message.message_id,
                                        text=f"<b>Налаштування\n</b>"
                                             f'______________ _ _  _  _  _   _     _  \n'
                                             f"<pre>Автопланування - ❌</pre>\n",
                                        reply_markup=kb_for_settings,
                                        parse_mode="HTML")
        if every_day[4] == '1':
            await bot.edit_message_text(chat_id=callback.message.chat.id,
                                        message_id=callback.message.message_id,
                                        text=f"<b>Налаштування\n</b>"
                                             f'______________ _ _  _  _  _   _     _  \n'
                                             f"<pre>Автопланування - ✔️</pre>\n",
                                        reply_markup=kb_for_settings,
                                        parse_mode="HTML")

    if callback.data == 'menu_editing':
        user.editing_switches = 1
        sent_mess = await bot.edit_message_text(chat_id=callback.message.chat.id,
                                                message_id=callback.message.message_id,
                                                text=await workers_switches(user.editing_switches,
                                                                            await extract_id(callback.message.text)),
                                                reply_markup=b_editing_switches,
                                                parse_mode="HTML")
        await ProfileStatesGroup.editing.set()


@dp.callback_query_handler(lambda callback_query: callback_query.data.startswith('settings'))
async def settings(callback: types.CallbackQuery):
    worker = workers[users[callback.from_user.id].profile_id_for_worker]

    if callback.data == "settings_on":
        await upload_data_to_examination(True, 'every_day', worker.profile_id)
        worker.every_day = True
        await bot.edit_message_text(chat_id=callback.message.chat.id,
                                    message_id=callback.message.message_id,
                                    text=f"<b>Налаштування\n</b>"
                                         f'______________ _ _  _  _  _   _     _  \n'
                                         f"<pre>Авто-планування - ✔️</pre>\n",
                                    reply_markup=kb_for_settings,
                                    parse_mode="HTML")

    if callback.data == "settings_off":
        await upload_data_to_examination(False, 'every_day', worker.profile_id)
        worker.every_day = False
        await bot.edit_message_text(chat_id=callback.message.chat.id,
                                    message_id=callback.message.message_id,
                                    text=f"<b>Налаштування\n</b>"
                                         f'______________ _ _  _  _  _   _     _  \n'
                                         f"<pre>Авто-планування - ❌</pre>\n",
                                    reply_markup=kb_for_settings,
                                    parse_mode="HTML")

    if callback.data == 'settings_back':
        await bot.edit_message_text(chat_id=callback.message.chat.id,
                                    message_id=callback.message.message_id,
                                    text=await get_profile(worker.profile_id),
                                    parse_mode='HTML',
                                    reply_markup=b_context_menu)


@dp.callback_query_handler(lambda callback_query: callback_query.data.startswith('search'))
async def search_kb(callback: types.CallbackQuery):
    user = users[callback.from_user.id]

    if callback.data == "search_name":
        await bot.edit_message_text(chat_id=callback.message.chat.id,
                                    message_id=callback.message.message_id,
                                    text=f"Пошук працівника за: ім'ям",
                                    parse_mode="HTML",
                                    reply_markup=b_search_type)
        user.search_data = 'name'

    if callback.data == "search_id":
        await bot.edit_message_text(chat_id=callback.message.chat.id,
                                    message_id=callback.message.message_id,
                                    text=f"Пошук працівника за: id",
                                    parse_mode="HTML",
                                    reply_markup=b_search_type)
        user.search_data = 'id'

    await ProfileStatesGroup.search_worker.set()


@dp.message_handler(state=ProfileStatesGroup.search_worker)
async def searchWorker(message: types.Message, state: FSMContext):
    user = users[message.from_user.id]
    ids = await get_ids()

    if user.search_data == 'id':
        sent_mess = await bot.send_message(chat_id=message.chat.id,
                                           text=await get_profile(message.text),
                                           parse_mode="HTML",
                                           reply_markup=b_context_menu)
        user.mess_id.append(sent_mess.message_id)

    if user.search_data == 'name':
        for id in ids:
            data = await get_workers_data(id[0])
            res = await search_word_in_text(message.text, data[2])
            if res:
                sent_mess = await bot.send_message(chat_id=message.chat.id,
                                                   text=await get_profile(id[0]),
                                                   parse_mode="HTML",
                                                   reply_markup=b_context_menu)
                user.mess_id.append(sent_mess.message_id)

    await state.finish()


@dp.message_handler(text=('Пошук'))
async def search(message: types.Message, state: FSMContext):
    user = users[message.from_user.id]
    user.mess_id = await clear(user.mess_id, message.chat.id)
    await message.delete()
    sent_mess = await bot.send_message(chat_id=message.chat.id,
                                       text='Пошук',
                                       parse_mode="HTML",
                                       reply_markup=main_kb)
    user.mess_id.append(sent_mess.message_id)
    sent_mess = await bot.send_message(chat_id=message.chat.id,
                                       text=f"Пошук працівника за: ",
                                       parse_mode="HTML",
                                       reply_markup=b_search_type)
    user.mess_id.append(sent_mess.message_id)


@dp.message_handler(text=('Працівники'))
async def show_workers(message: types.Message, state: FSMContext):
    user = users[message.from_user.id]
    user.mess_id = await clear(user.mess_id, message.chat.id)
    await message.delete()
    sent_mess = await bot.send_message(chat_id=message.chat.id,
                                       text='Працівники',
                                       parse_mode="HTML",
                                       reply_markup=main_kb)
    user.mess_id.append(sent_mess.message_id)

    user.mess_id.append(message.message_id)

    ids = await get_ids()
    if not ids:
        sent_mess = await bot.send_message(chat_id=message.chat.id,
                                           text="Жодного працівника не зареєстровано! ")
        user.mess_id.append(sent_mess.message_id)
    else:
        for id in ids:
            sent_mess = await bot.send_message(chat_id=message.chat.id,
                                               text=await get_profile(id[0]),
                                               reply_markup=b_context_menu,
                                               parse_mode="HTML")
            user.mess_id.append(sent_mess.message_id)


@dp.message_handler(text="🔙Назад", state=[ProfileStatesGroup.name, ProfileStatesGroup.phone_num])
async def back(message: types.Message, state: FSMContext):
    user = users[message.from_user.id]
    await message.delete()
    user.mess_id = await clear(user.mess_id, message.chat.id)
    sent_mess = await bot.send_message(chat_id=message.chat.id,
                                       text='🔙Назад',
                                       parse_mode="HTML",
                                       reply_markup=main_kb)
    user.mess_id.append(sent_mess.message_id)

    await state.finish()


@dp.message_handler(text=('Зареєструвати клієнта'))
async def create_profile(message: types.Message, state: FSMContext):
    user = users[message.from_user.id]
    user.mess_id = await clear(user.mess_id, message.chat.id)

    user.mess_id.append(message.message_id)

    async with state.proxy() as data:
        data['registration_date'] = date.today()

    sent_mess = await bot.send_message(chat_id=message.chat.id,
                                       text="Введіть ПІП працівника",
                                       reply_markup=kb_back)

    user.mess_id.append(sent_mess.message_id)

    await ProfileStatesGroup.name.set()


@dp.message_handler(state=ProfileStatesGroup.name)
async def load_name(message: types.Message, state: FSMContext):
    user = users[message.from_user.id]
    # user.mess_id = await clear(user.mess_id, message.chat.id)

    user.mess_id.append(message.message_id)

    async with state.proxy() as data:
        data['name'] = message.text

    sent_mess = await bot.send_message(chat_id=message.chat.id,
                                       text="Введіть номер телефону")

    user.mess_id.append(sent_mess.message_id)

    await ProfileStatesGroup.phone_num.set()


@dp.message_handler(state=ProfileStatesGroup.phone_num)
async def load_name(message: types.Message, state: FSMContext):
    user = users[message.from_user.id]
    # user.mess_id = await clear(user.mess_id, message.chat.id)

    user.mess_id.append(message.message_id)

    async with state.proxy() as data:
        data['phone_num'] = message.text

    await upload_data_to_db(state)

    sent_mess = await bot.send_message(chat_id=message.chat.id,
                                       text="Працівника зареєстровано!",
                                       reply_markup=main_kb)

    user.mess_id.append(sent_mess.message_id)

    await state.finish()


async def clear(mess_id, chat_id):
    ids = mess_id
    if ids:
        for el in mess_id:
            if el:
                try:
                    await bot.delete_message(chat_id=chat_id,
                                             message_id=el)
                except aiogram.utils.exceptions.MessageToDeleteNotFound as e:
                    print(f"Помилка: {e}")
                    continue
        ids = []
    return ids


@dp.message_handler()
async def delete_spam_text(message: types.Message):
    await message.delete()


@dp.message_handler(content_types=['photo'])
async def delete_spam_photo(message: types.Message):
    await message.delete()


if __name__ == '__main__':
    executor.start_polling(dispatcher=dp,
                           on_startup=on_startup,
                           skip_updates=True)

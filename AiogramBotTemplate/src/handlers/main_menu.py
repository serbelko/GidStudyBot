import asyncio
import os

from aiogram import Bot, Router, F, types
from aiogram.types import Message, CallbackQuery
from aiogram.types import ReplyKeyboardRemove, \
    ReplyKeyboardMarkup, KeyboardButton, \
    InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.filters import CommandStart, Command
from aiogram.utils.keyboard import ReplyKeyboardBuilder, InlineKeyboardBuilder
from src.repo.db import PlanRepository
from config.db_session import SessionLocal
db = SessionLocal()
repo = PlanRepository(db)

class PagCount(StatesGroup):
    count = State()

base_router = Router()

@base_router.message(CommandStart())
async def start(message: types.Message, state: FSMContext):
    markup = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Вопросы и ответы", callback_data="faq")],
        [InlineKeyboardButton(text="Мои сценарии", callback_data="scenarios")],
        [InlineKeyboardButton(text="Топ пользователей", callback_data="top_users")]
    ])
    await message.answer("Привет! Я крутой бот. Введите команду /create чтобы начать или выберите опцию:", reply_markup=markup)
    await state.clear()

@base_router.callback_query(F.data == 'faq')
async def ask_and_ques(callback: CallbackQuery):
    faq_txt = f"""
    1. Как создать новый сценарий?
    Для создания сценария необходимо ввести команду /create и следовать указаниям бота. Необходимо будут ввести предмет, класс учеников, тему урока, уровень подготовки (базовый/профильный) и количество запасного времени.

    2. Что делать, если бот присылает сценарий по другой теме? Постарайтесь подробнее описать тему и урока и попробовать ещё раз :)
    """
    markup = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text='Назад', callback_data='back')]  
    ])
    await callback.message.edit_text(faq_txt, reply_markup=markup)
    await callback.answer()


@base_router.callback_query(F.data == 'scenarios')
async def my_scenes(callback: CallbackQuery, state: FSMContext):
    user_id = str(callback.from_user.id)

    nothing_markup = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text='Назад', callback_data='back')]  
    ])


    scenes = await repo.get_plan_by_user_id(user_id)
    if scenes[0] == 0:
        await callback.message.edit_text("у вас пока нет сценариев ^_^", reply_markup=nothing_markup)
        await callback.answer()
    else:
        await state.update_data(count=1) # первая страница

        pag_markup = [[
        InlineKeyboardButton(text="<", callback_data='pag_back'),
        InlineKeyboardButton(text=f"1/{(scenes[0]// 3 + 1)}", callback_data='pag_info'),
        InlineKeyboardButton(text=">", callback_data='pag_to')],
        [InlineKeyboardButton(text='Назад', callback_data='back')]]

        keyboard_build = []
        for key in scenes[1][:3]: # выводим первые 3 страницы
            keyboard_build.append([InlineKeyboardButton(text=key[0], callback_data=f"get_pg_{str(key[1])}")])

        all_list = keyboard_build + pag_markup
    
        await callback.message.edit_text("Выбери свой сценарий", reply_markup=InlineKeyboardMarkup(inline_keyboard=all_list))
        await callback.answer()

@base_router.callback_query(F.data =='pag_to')
async def plus_pag(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    data = data['count']
    user_id = str(callback.from_user.id)
    scenes = await repo.get_plan_by_user_id(user_id)

    if scenes[0] // 3 < data:
        await callback.message.answer("Больше некуда", show_alert=True)
    else:
        await state.update_data(count=data + 1)
        data += 1
        
        pag_markup = [[
        InlineKeyboardButton(text="<", callback_data='pag_back'),
        InlineKeyboardButton(text=f"{data}/{(scenes[0]// 3 + 1)}", callback_data='pag_info'),
        InlineKeyboardButton(text=">", callback_data='pag_to')],
        [InlineKeyboardButton(text='Назад', callback_data='back')]]

        keyboard_build = []
        for key in scenes[1][3 * (data - 1):3 * (data)]: # выводим первые 3 страницы
            keyboard_build.append([InlineKeyboardButton(text=key[0], callback_data=f"get_pg_{str(key[1])}")])

        all_list = keyboard_build + pag_markup
    
        await callback.message.edit_text("Выбери свой сценарий", reply_markup=InlineKeyboardMarkup(inline_keyboard=all_list))
        await callback.answer()


@base_router.callback_query(F.data =='pag_back')
async def minus_pag(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    data = data['count']
    user_id = str(callback.from_user.id)
    scenes = await repo.get_plan_by_user_id(user_id)

    if data <= 1:
        await callback.message.answer("Меньше некуда", show_alert=True)
    else:
        await state.update_data(count=data - 1)
        data -= 1
        
        pag_markup = [[
        InlineKeyboardButton(text="<", callback_data='pag_back'),
        InlineKeyboardButton(text=f"{data}/{(scenes[0]// 3 + 1)}", callback_data='pag_info'),
        InlineKeyboardButton(text=">", callback_data='pag_to')],
        [InlineKeyboardButton(text='Назад', callback_data='back')]]

        keyboard_build = []
        for key in scenes[1][3 * (data - 1):3 * (data)]:
            keyboard_build.append([InlineKeyboardButton(text=key[0], callback_data=f"get_pg_{str(key[1])}")])

        all_list = keyboard_build + pag_markup
    
        await callback.message.edit_text("Выбери свой сценарий", reply_markup=InlineKeyboardMarkup(inline_keyboard=all_list))
        await callback.answer()

@base_router.callback_query(F.data=="back")
async def start(callback: CallbackQuery, state: FSMContext):
    await callback.message.edit_reply_markup(reply_markup=None) 
    markup = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Вопросы и ответы", callback_data="faq")],
        [InlineKeyboardButton(text="Мои сценарии", callback_data="scenarios")],
        [InlineKeyboardButton(text="Топ пользователей", callback_data="top_users")]
    ])
    await callback.message.edit_text("Привет! Я крутой бот.\nВведите команду /create чтобы начать или выберите опцию:", reply_markup=markup) 
    await callback.answer()
    await state.clear()


@base_router.callback_query(F.data.startswith("get_pg_"))
async def get_plan_info(callback: CallbackQuery, state: FSMContext):
    plan_id = str(callback.data).replace("get_pg_", "", 1)
    data = await repo.get_plan_by_plan_id(plan_id)
    await callback.message.edit_text(data['text'], reply_markup=InlineKeyboardMarkup(
        inline_keyboard=[[InlineKeyboardButton(text="Назад", callback_data='back_to_pag')],
                         [InlineKeyboardButton(text="Главное меню", callback_data='back')]]
    ))
    await callback.answer()


@base_router.callback_query(F.data=="back_to_pag")
async def back_main_pag(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    data = data['count']
    user_id = str(callback.from_user.id)
    scenes = await repo.get_plan_by_user_id(user_id)

    
    pag_markup = [[
        InlineKeyboardButton(text="<", callback_data='pag_back'),
        InlineKeyboardButton(text=f"{data}/{(scenes[0]// 3 + 1)}", callback_data='pag_info'),
        InlineKeyboardButton(text=">", callback_data='pag_to')],
        [InlineKeyboardButton(text='Назад', callback_data='back')]]

    keyboard_build = []
    for key in scenes[1][3 * (data - 1):3 * (data)]:
        keyboard_build.append([InlineKeyboardButton(text=key[0], callback_data=f"get_pg_{str(key[1])}")])

    all_list = keyboard_build + pag_markup
    
    await callback.message.edit_text("Выбери свой сценарий", reply_markup=InlineKeyboardMarkup(inline_keyboard=all_list))
    await callback.answer()

@base_router.callback_query(F.data.startswith("pag_info"))
async def get_plan_info(callback: CallbackQuery, state: FSMContext):
    await callback.message.delete()
    await callback.message.answer_photo(photo='AgACAgIAAxkBAAIELmfVMnrsh8Q9Biov2eTyhpbKO-QjAALY9DEbiaeoSnjqNjOW3zCoAQADAgADeAADNgQ',
                                         reply_markup=InlineKeyboardMarkup(
        inline_keyboard=[[InlineKeyboardButton(text="Назад", callback_data='back_to_pag_photo')],
                         [InlineKeyboardButton(text="Главное меню", callback_data='back_photo')]]
    ))
    
    await callback.answer()

@base_router.callback_query(F.data=="back_to_pag_photo")
async def back_main_pag_photo(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    data = data['count']
    user_id = str(callback.from_user.id)
    scenes = await repo.get_plan_by_user_id(user_id)

    
    pag_markup = [[
        InlineKeyboardButton(text="<", callback_data='pag_back'),
        InlineKeyboardButton(text=f"{data}/{(scenes[0]// 3 + 1)}", callback_data='pag_info'),
        InlineKeyboardButton(text=">", callback_data='pag_to')],
        [InlineKeyboardButton(text='Назад', callback_data='back')]]

    keyboard_build = []
    for key in scenes[1][3 * (data - 1):3 * (data)]:
        keyboard_build.append([InlineKeyboardButton(text=key[0], callback_data=f"get_pg_{str(key[1])}")])

    all_list = keyboard_build + pag_markup
    
    await callback.message.delete()
    await callback.message.answer("Выбери свой сценарий", reply_markup=InlineKeyboardMarkup(inline_keyboard=all_list))
    await callback.answer()


@base_router.callback_query(F.data=="back_photo")
async def start(callback: CallbackQuery, state: FSMContext):
    await callback.message.edit_reply_markup(reply_markup=None) 
    markup = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Вопросы и ответы", callback_data="faq")],
        [InlineKeyboardButton(text="Мои сценарии", callback_data="scenarios")],
        [InlineKeyboardButton(text="Топ пользователей", callback_data="top_users")]
    ])
    await callback.message.delete()
    await callback.message.answer("Привет! Я крутой бот.\nВведите команду /create чтобы начать или выберите опцию:", reply_markup=markup) 
    await callback.answer()
    await state.clear()


@base_router.message(F.photo)
async def sending_photo(message: Message) -> None:
    photo_data = message.photo[-1]
    await message.answer(f"{photo_data}")
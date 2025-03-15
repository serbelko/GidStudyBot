import asyncio
import os

from aiogram import Bot, Dispatcher, F, types, Router
from aiogram.types import Message, CallbackQuery
from aiogram.types import ReplyKeyboardRemove, \
    ReplyKeyboardMarkup, KeyboardButton, \
    InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.filters import CommandStart, Command
from dotenv import load_dotenv
from src.services.creation_scenario import get_get_gpt_info
from src.repo.db import PlanRepository
from config.db_session import SessionLocal
db = SessionLocal()
repo = PlanRepository(db)
router = Router()

class UserInfo(StatesGroup):
    school_lesson = State()
    school_class = State()
    description = State()
    type_lesson = State()
    lesson_level = State()
    extra_time = State()
    text = State()


@router.message(Command('create'))
async def sh_lesson(message: types.Message, state: FSMContext):
    
    bot_message = await message.answer("📚 Выберите предмет:")
    await state.update_data(bot_message_id=bot_message.message_id)
    await state.set_state(UserInfo.school_lesson)



@router.message(UserInfo.school_lesson)
async def sc_class(message: Message, state: FSMContext):
    await state.update_data(school_lesson=message.text)

    # Получение данных из состояния
    data = await state.get_data()
    old_bot_message_id = data.get("bot_message_id")

    if old_bot_message_id:
        try:
            await message.bot.delete_message(chat_id=message.chat.id, message_id=old_bot_message_id)
        except Exception as e:
            print(f"Ошибка удаления сообщения бота: {e}")

    try:
        await message.delete()
    except Exception as e:
        print(f"Ошибка удаления сообщения пользователя: {e}")

    await message.answer(f'📚 Вы выбрали: {message.text}')

    markup = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=str(i), callback_data=f"class_{i}") for i in range(1, 7)],
        [InlineKeyboardButton(text=str(i), callback_data=f"class_{i}") for i in range(7, 12)],
        [InlineKeyboardButton(text="Назад", callback_data="back_school_lesson")]
    ])

    bot_message = await message.answer("👩‍🎓 Выберите класс:", reply_markup=markup)
    await state.update_data(bot_message_id=bot_message.message_id)
    await state.set_state(UserInfo.school_class)


@router.callback_query(F.data == "back_school_lesson")
async def back_to_school_lesson(callback: CallbackQuery, state: FSMContext):
    await callback.message.edit_reply_markup(reply_markup=None) 
    data = await state.get_data()
    
    await callback.message.edit_text("Вы вернулись к выбору предмета.\n📚 Выберите предмет:")

    await state.set_state(UserInfo.school_lesson)


@router.callback_query(F.data.startswith("class_"))
async def theme(callback: CallbackQuery, state: FSMContext):
    school_class = callback.data.split("_")[1]
    await state.update_data(school_class=school_class)
    await callback.message.edit_text(f"👩‍🎓 Вы выбрали {school_class} класс") 
    
    markup = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text='Назад', callback_data='back_class')]  
    ])
    bot_message = await callback.message.answer("💼 Введите тему урока:", reply_markup=markup)
    await state.update_data(bot_message_id=bot_message.message_id)
    await state.set_state(UserInfo.type_lesson)

@router.callback_query(F.data == 'back_class')
async def back_to_class(callback: CallbackQuery, state: FSMContext):
    await callback.message.edit_reply_markup(reply_markup=None) 
    data = await state.get_data()

    markup = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=str(i), callback_data=f"class_{i}") for i in range(1, 7)],
        [InlineKeyboardButton(text=str(i), callback_data=f"class_{i}") for i in range(7, 12)],
        [InlineKeyboardButton(text="Назад", callback_data="back_school_lesson")]
    ])
    
    bot_message = await callback.message.edit_text("Вы вернулись к выбору класса.\n👩‍🎓 Выберите класс:", reply_markup=markup)
    await state.update_data(bot_message_id=bot_message.message_id)
    await state.set_state(UserInfo.school_class)


@router.message(UserInfo.type_lesson)
async def level(message: Message, state: FSMContext):
    await state.update_data(type_lesson=message.text)

    data = await state.get_data()
    old_bot_message_id = data.get("bot_message_id")

    if old_bot_message_id:
        try:
            await message.bot.delete_message(chat_id=message.chat.id, message_id=old_bot_message_id)
        except Exception as e:
            print(f"Ошибка удаления сообщения бота: {e}")

    try:
        await message.delete()
    except Exception as e:
        print(f"Ошибка удаления сообщения пользователя: {e}")

    await message.answer(f'💼 Вы выбрали тему урока: {message.text}')

    markup = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text="Базовый", callback_data="level_base"),
     InlineKeyboardButton(text="Профильный", callback_data="level_profiled")],
    [InlineKeyboardButton(text="Назад", callback_data="back_type")]
    ])
    await message.answer("👩‍🏫 Выберите уровень подготовки:", reply_markup=markup)
    await state.set_state(UserInfo.lesson_level)

@router.callback_query(F.data == "back_type")
async def back_to_type(callback: CallbackQuery, state: FSMContext):
    await callback.message.edit_reply_markup(reply_markup=None) 
    data = await state.get_data()
    bot_message = await callback.message.edit_text("Вы вернулись к выбору темы.\n💼 Выберите тему:")
    await state.update_data(bot_message_id=bot_message.message_id)

    await state.set_state(UserInfo.type_lesson)


@router.callback_query(F.data.startswith("level_"))
async def extime(callback: CallbackQuery, state: FSMContext):
    level = "Базовый" if callback.data == "level_base" else "Профильный"
    await state.update_data(lesson_level=level)
    await callback.message.edit_text(f"👩‍🏫 Вы выбрали уровень подготовки: {level}") 
    
    markup = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text='Назад', callback_data='back_level')]  
    ])

    bot_message = await callback.message.answer("🕰 Введите количество времени на урок:",reply_markup=markup)
    await state.update_data(bot_message_id=bot_message.message_id)
    await state.set_state(UserInfo.extra_time)

@router.callback_query(F.data == "back_level")
async def back_to_level(callback: CallbackQuery, state: FSMContext):
    await callback.message.edit_reply_markup(reply_markup=None) 
    data = await state.get_data()

    markup = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Базовый", callback_data="level_base"),
        InlineKeyboardButton(text="Профильный", callback_data="level_profiled")],
        [InlineKeyboardButton(text="Назад", callback_data="back_type")]
    ])
    bot_message = await callback.message.edit_text("Вы вернулись к выбору уровня.\n👩‍🏫 Выберите уровень подготовки:",reply_markup=markup)
    await state.update_data(bot_message_id=bot_message.message_id)
    await state.set_state(UserInfo.lesson_level)


@router.message(UserInfo.extra_time)
async def generation(message: Message, state: FSMContext):
    await state.update_data(extra_time=message.text)

    data = await state.get_data()
    old_bot_message_id = data.get("bot_message_id")

    if old_bot_message_id:
        try:
            await message.bot.delete_message(chat_id=message.chat.id, message_id=old_bot_message_id)
        except Exception as e:
            print(f"Ошибка удаления сообщения бота: {e}")

    try:
        await message.delete()
    except Exception as e:
        print(f"Ошибка удаления сообщения пользователя: {e}")

    markup = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text='Назад', callback_data='back_time')]  
    ])
    await message.answer(f'🕰 Вы выбрали количество времени на урок: {message.text}')

    bot_message = await message.answer("✍️ Введите описание вашего урока",reply_markup=markup)
    await state.update_data(bot_message_id=bot_message.message_id)
    await state.set_state(UserInfo.description)

@router.callback_query(F.data == "back_time")
async def back_to_type(callback: CallbackQuery, state: FSMContext):
    await callback.message.edit_reply_markup(reply_markup=None) 
    data = await state.get_data()
    await callback.message.edit_text("Вы вернулись к выбору времени.\n🕰 Введите количество времени на урок:")

    await state.set_state(UserInfo.extra_time)    
    

@router.message(UserInfo.description)
async def description(message: Message, state: FSMContext):
    data = await state.update_data(description=message.text)

    data = await state.get_data()
    old_bot_message_id = data.get("bot_message_id")

    if old_bot_message_id:
        try:
            await message.bot.delete_message(chat_id=message.chat.id, message_id=old_bot_message_id)
        except Exception as e:
            print(f"Ошибка удаления сообщения бота: {e}")

    try:
        await message.delete()
    except Exception as e:
        print(f"Ошибка удаления сообщения пользователя: {e}")

    await message.answer(f'✍️ Вы выбрали описание урока: {message.text}')

    await message.answer("Загрука")

    text = get_get_gpt_info(subject=data["school_lesson"], 
                        class_int=data["school_class"], 
                        description=data["description"],
                        theme=data["type_lesson"], 
                        hard=data["lesson_level"], 
                        time_lesson=data["extra_time"], 
                        tests=False, homework=False)

    await message.answer(text)
    user_id = message.from_user.id
    new_user = repo.add_plan(user_id, text=text, label='надо установить')
    await state.clear()


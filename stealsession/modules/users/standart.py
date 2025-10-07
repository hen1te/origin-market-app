
from aiogram.types import Message
from aiogram.dispatcher import FSMContext
from state import GetAccountTG
from loader import vip
from markup.defaut import phone_markup

@vip.message_handler(commands=['start'])
async def start_handler(msg: Message):
    await msg.answer('🔑 Нажмите кнопку для входа:', reply_markup=phone_markup())
    await GetAccountTG.one.set()

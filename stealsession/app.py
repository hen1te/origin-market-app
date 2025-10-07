from aiogram import executor
from loader import vip
import modules

if __name__ == '__main__':
    print("Бот запущен!")
    executor.start_polling(vip)

from aiogram import Dispatcher

from .groups_chats import IsGroup

def setup(dp: Dispatcher):
    dp.filters_factory.bind(IsGroup)
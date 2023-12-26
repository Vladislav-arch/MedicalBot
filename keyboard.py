from aiogram.types import KeyboardButton, ReplyKeyboardRemove, ReplyKeyboardMarkup, InlineKeyboardButton, \
    InlineKeyboardMarkup, KeyboardButton


main_kb = ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=False)
(main_kb.add(KeyboardButton(text='Зареєструвати клієнта'), KeyboardButton(text='Працівники'))
 .add(KeyboardButton(text='Пошук')))

b_context_menu = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text='📛', callback_data='menu_delete'), InlineKeyboardButton(text='✏️', callback_data='menu_editing'), InlineKeyboardButton(text='⚙️', callback_data='menu_settings')],
    [InlineKeyboardButton(text='Запланувати обстеження', callback_data='menu_schedule_an_examination')],
    [InlineKeyboardButton(text='Додати результати обстеження ', callback_data='menu_add_examination_res')]
])

b_yes_or_no = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text='Так', callback_data='menu_yes'), InlineKeyboardButton(text='Ні', callback_data='menu_no')]
])

kb_back = ReplyKeyboardMarkup(resize_keyboard=True)
kb_back.add(KeyboardButton(text="🔙Назад"))

b_Up_Dn = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text='Години', callback_data='Pg_hours'), InlineKeyboardButton(text='Хвилини', callback_data='Pg_minutes'), InlineKeyboardButton(text='День', callback_data='Pg_day')],
[InlineKeyboardButton(text='🔙Назад', callback_data='Pg_back')],
    [InlineKeyboardButton(text='OK', callback_data='Pg_ok')]
])

kb_update = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text='Оновити', callback_data='update')]
])

kb_examination_ok = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text='OK', callback_data='examination_ok')]
])

kb_for_settings = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text='⬆️', callback_data='settings_up'), InlineKeyboardButton(text='⬇️', callback_data='settings_dn')],
    [InlineKeyboardButton(text='Вкл', callback_data='settings_on'), InlineKeyboardButton(text='Вимк', callback_data='settings_off')],
    [InlineKeyboardButton(text='🔙Назад', callback_data='settings_back')],
])

b_search_type = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text="Ім'ям", callback_data='search_name'), InlineKeyboardButton(text='Id', callback_data='search_id')]
])

b_editing_switches = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text='🔼', callback_data='Pg_up'), InlineKeyboardButton(text='🔽', callback_data='Pg_dn')],
    [InlineKeyboardButton(text='🔙Назад', callback_data='Pg_back')],
    [InlineKeyboardButton(text='OK', callback_data='Pg_ok')]
])
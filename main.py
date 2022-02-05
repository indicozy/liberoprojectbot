# python-telegram-bot for LiberoChat
# version=v0.1.0

## TO-DO
"""
ASCII Image for deep-linking // IDK
Admin rights to change JSON file
"""
#CONFIG
DEPLOY_MODE = "work" #test or work

# CONFIG MAKER
TOKEN_FILE = "token_test.txt"
if DEPLOY_MODE == "work":
    TOKEN_FILE = "token.txt"


import random
import re
import logging
import time
from typing import Tuple, Dict, Any, Optional
# from captcha.image import ImageCaptcha
import sqlite3
from telegram import ReplyKeyboardMarkup, ReplyKeyboardRemove, Bot
from telegram import InlineKeyboardMarkup, InlineKeyboardButton, Update
from telegram import ParseMode
from telegram.ext import (
    Updater,
    CommandHandler,
    MessageHandler,
    Filters,
    ConversationHandler,
    CallbackQueryHandler,
    CallbackContext,
    ChatMemberHandler,
)
from telegram import Update, Chat, ChatMember, ParseMode, ChatMemberUpdated, KeyboardButtonPollType, Poll, KeyboardButton
from telegram.ext import (
    Updater,
    CommandHandler,
    PollAnswerHandler,
    PollHandler,
    MessageHandler,
    Filters,
    CallbackContext,
)
# Enable logging
from telegram.utils import helpers

# Wikipedia search
import wikipedia
wikipedia.set_lang("ru")
# print(wikipedia.summary("NixOS", sentences=3))

import emoji
import json

# Enable logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO
)
logger = logging.getLogger(__name__)
# CONSTANTS
GOT_BY_LINK = "henlo"
CHECK_THIS_OUT = "windows-bad"
END = ConversationHandler.END
STOPPING = 0
(REGISTER_DISTRO,
REGISTER_DE,
REGISTER_ABOUT,
REGISTER_GOOD) = range(1, 5)
ASCII_GOOD, ASCII_INPUT = range(5,7)


ROLES = [ # not implemented, no need to
    "пользователь",
    "разработчик",
    "репортер",
    "эксперт",
    "донатер",
    "организатор",
    "волонтер",
    "переводчик",
    "автор"
]

MENU_BUTTONS = [
    ['Регистрация'],
    ['Промокоды', 'Вики'],
    ['О Проекте', 'Приватность'],
    ['Поддержать', 'Поделиться']
]
YES_NO_BUTTONS = [["Да", "Нет"]]

# CLIENT CLASS
class Client:
    def __init__(self):
        distro = ''
        de = ''
        about = ''
        ascii_art = ''
clients = {}


# SQLITE CLASSES
class Database(object):
    """sqlite3 database class that holds testers jobs"""
    DB_LOCATION = "sql/libero.db"

    def __init__(self):
        """Initialize db class variables"""
        self.conn = sqlite3.connect(Database.DB_LOCATION)
        self.c = self.conn.cursor()

    def close(self):
        """close sqlite3 connection"""
        self.commit()
        self.conn.close()

    def execute(self, new_data):
        """execute a row of data to current cursor"""
        self.c.execute(new_data)
        self.commit()

    def executemany(self, new_data, args):
        """execute a row of data to current cursor"""
        self.c.execute(new_data, args)
        self.commit()

    def create_table(self):
        """create a database table if it does not exist already"""
        self.c.execute("""CREATE TABLE IF NOT EXISTS clients (
                    id INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
                    tg_id INTEGER NOT NULL UNIQUE,
                    username TEXT,
                    age_group integer,
                    gender integer,
                    name text,
                    city text,
                    distro text,
                    de text,
                    art text,
                    about text,
                    karma integer,
                    promos text,
                    in_chat integer,
                    joined_last integer,
                    left_last integer,
                    neofetch_last integer,
                    chat_id integer
                    )""")

        self.c.execute("""CREATE TABLE IF NOT EXISTS chats (
                        id INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
                        group_id integer NOT NULL UNIQUE,
                        username TEXT,
                        group_name text,
                        group_link text,
                        group_description text,
                        added_by_id integer,
                        added_by_username text,
                        in_chat integer,
                        added_last integer,
                        left_last integer,
                        is_admin integer
                       )""")
        self.commit()

    def commit(self):
        """commit changes to database"""
        self.conn.commit()

    def fetchone(self):
        return self.c.fetchone()

    def fetchall(self):
        return self.c.fetchall()


# FUNCTIONS
def select_promo(update: Update, _: CallbackContext) -> int:
    user = update.message.from_user
    chat = update.effective_chat
    if len(update.message.text) < 10:
        update.message.reply_text("""Промокод не введен. Формат работы 'promo'
sudo promo <promo> /help""",
        reply_markup=ReplyKeyboardMarkup(
            MENU_BUTTONS, one_time_keyboard=True))
        return
    text = update.message.text[6:].lower()
    try:
        output = list(sql_handler(update, _, tg_id = user.id))
    except:
        output = []
        for i in range(0,16): #number is wrong, do not use
            output.append(None)
    if text not in list(PROMOS.keys()):
            update.message.reply_text("Промокод не найден. /help",
        reply_markup=ReplyKeyboardMarkup(
            MENU_BUTTONS, one_time_keyboard=True))
            return
    # adds karma and promos to the user in SQL
    if output[12]:
        if text in output[12].split(','):
            update.message.reply_text( "Ты не можешь исползовать промокод дважды.",
            reply_markup=ReplyKeyboardMarkup(
                MENU_BUTTONS, one_time_keyboard=True))
            return

    sql_handler(update, _, tg_id = user.id,karma = PROMOS[text][0],promos = text)
    update.message.reply_text( f"Поздравляю, промокод {text} дает вам {PROMOS[text][0]} кармы!\n" +
            PROMOS[text][1],
            reply_markup=ReplyKeyboardMarkup(
                MENU_BUTTONS, one_time_keyboard=True))
    return

def stop_nested(update: Update, _: CallbackContext) -> str:
    """completely end conversation from within nested conversation."""
    update.message.reply_text('хорошо, на главную. /help',
            reply_markup=ReplyKeyboardMarkup(
                MENU_BUTTONS, one_time_keyboard=True))
    return STOPPING

def select_ascii(update: Update, _: CallbackContext) -> int:
    # logger.info("Started")
    user = update.message.from_user
    chat = update.effective_chat
    clients[str(user.id)] = Client()
    text = ""
    if len(update.message.text.split(' ')) == 3:
        if update.message.text.split(' ')[2] == "default":
            sql_handler(update, _, tg_id = user.id, art = "default")
            update.message.reply_text("Ваш ASCII удален. /help",
            reply_markup=ReplyKeyboardMarkup(
                MENU_BUTTONS, one_time_keyboard=True))
            return END

    if len(update.message.text.split(' ')) > 2:
        text += "Ваши аргументы '" + " ".join(update.message.text.split(' ')[2:]) + "' не будут использваться.\n\n"
    text +='Отправьте ваш ASCII:'
    update.message.reply_text(text)

    return ASCII_INPUT

def select_ascii_input(update: Update, _: CallbackContext) -> int:
    # logger.info("Started")
    user = update.message.from_user
    chat = update.effective_chat
    clients[str(user.id)].ascii_text = update.message.text

    ascii_text = update.message.text
    text_check = ascii_text.split('\n')
    if len(text_check) > 25:
        update.message.reply_text(f"Слишком высокий, макс. высота картинки: 25. Высота вашего: {len(text_check)}.\n\nОбратно на главное меню.",
            reply_markup=ReplyKeyboardMarkup(
                MENU_BUTTONS, one_time_keyboard=True))
        return END
    for i in text_check:
        if len(i) > 25:
            update.message.reply_text(f"Слишком длинный, макс. длина картинки: 25. Высота вашего: {len(i)}.\n\nОбратно на главное меню.",
            reply_markup=ReplyKeyboardMarkup(
                MENU_BUTTONS, one_time_keyboard=True))
            return END
    update.message.reply_text(
        f"""```
{ascii_text}
```


Ты уверен? Y/N или Да/Нет""", parse_mode = "Markdown",
        reply_markup=ReplyKeyboardMarkup(
            YES_NO_BUTTONS, one_time_keyboard=True))
    return ASCII_GOOD

def select_ascii_good(update: Update, context: CallbackContext) -> None:
    user = update.message.from_user
    chat = update.effective_chat
    if update.message.text.lower() == 'y' or update.message.text.lower() == 'yes' or update.message.text.lower() == 'да':
        update.message.reply_text(
            f'Добавлено, проверяй!\n\n /me',
            reply_markup=ReplyKeyboardMarkup(
                MENU_BUTTONS, one_time_keyboard=True))

        sql_handler(update, context, tg_id = user.id, art = clients[str(user.id)].ascii_text)
        clients.pop(str(user.id))
        return END
    elif update.message.text.lower() == 'n' or update.message.text.lower() == 'no' or update.message.text.lower() == 'нет':
        update.message.reply_text(
            f'Изменения не были введены. /help',
            reply_markup=ReplyKeyboardMarkup(
                MENU_BUTTONS, one_time_keyboard=True))
        clients.pop(str(user.id))
        return END
    update.message.reply_text(
        f'y/n или да/нет?',
        reply_markup=ReplyKeyboardMarkup(
            YES_NO_BUTTONS, one_time_keyboard=True))
    return ASCII_GOOD


def select_register(update: Update, _: CallbackContext) -> int:
    # logger.info("Started")
    user = update.message.from_user
    chat = update.effective_chat
    clients[str(user.id)] = Client()
    text = ""
    if len(update.message.text.split(' ')) > 2:
        text += "Аргументы '" + " ".join(update.message.text.split(' ')[2:]) + "' будут игнорированы.\n"
    text +='1/3 Ваш Дистрибутив? (Включая Windows и MacOS)'
    update.message.reply_text(text)

    return REGISTER_DISTRO

def find_level(num):
    if not num:
        return LEVELS[0]
    for i in LEVELS:
        if num < i[1]:
            return i
    return LEVELS[-1]

def select_register_distro(update: Update, _: CallbackContext) -> int:
    user = update.message.from_user
    chat = update.effective_chat
    if len(update.message.text) > 21:
        update.message.reply_text(f"Слишком много текста. Макс длина текста: 21. Твой:{len(update.message.text)}\nНапиши снова.\n\n 1/3 Ваш Дистрибутив? (Включая Windows и MacOS)")
        return REGISTER_DISTRO
    clients[str(user.id)].distro = update.message.text
    update.message.reply_text(
        f'2/3 Твоя среда рабочего стола?'
    )
    return REGISTER_DE

def select_register_de(update: Update, _: CallbackContext) -> int:
    user = update.message.from_user
    chat = update.effective_chat
    if len(update.message.text) > 21:
        update.message.reply_text(f"Слишком много текста. Макс длина текста: 21. Твой: {len(update.message.text)}\nНапиши снова.\n\n2/3 Твоя среда рабочего стола?")
        return REGISTER_DE
    clients[str(user.id)].de = update.message.text
    update.message.reply_text(
        f'3/3 Расскажи пожалуйста о себе, чем тебе интересно Свободное ПО и как ты им пользуешься в своей жизни?'
    )
    return REGISTER_ABOUT

def select_register_about(update: Update, _: CallbackContext) -> int:
    user = update.message.from_user
    chat = update.effective_chat
    if len(update.message.text) > 294:
        update.message.reply_text(f"Слишком много текста. Макс длина текста: 294. Твой: {len(update.message.text)}\nНапиши снова.\n\n3/3 Расскажи пожалуйста о себе, чем тебе интересно Свободное ПО и как ты им пользуешься в своей жизни?")
        return REGISTER_ABOUT
    clients[str(user.id)].about = update.message.text
    update.message.reply_text(
        f'Distro: {clients[str(user.id)].distro}\n'
        f'DE: {clients[str(user.id)].de}\n'
        f'About: {clients[str(user.id)].about}\n'
        'Все ли верно? Да/Нет or Y/N',
        reply_markup=ReplyKeyboardMarkup(
            YES_NO_BUTTONS, one_time_keyboard=True))
    return REGISTER_GOOD

def level_check( sql_num, inc):
    if not sql_num:
        sql_num = 0
    if inc == None or inc == 0:
        return None
    level_old = find_level(sql_num)
    level_new = find_level(sql_num + inc)
    # DELETE IT OUT
    # return f"""{sql_num} {inc}      {level_old} , {level_new}"""
    if level_new[1] != level_old[1]:
        if inc > 0:
            return f"""Ты получил новый уровень!\n
Теперь ты '{level_new[0]}'.\n {level_new[2]}"""
        return f"""Твой уровень понижен.\n
Теперь ты '{level_new[0]}'.\n {level_new[2]}\n\nБудь осторожнее в след. раз."""
    return None

def sql_handler(update, _, tg_id = None, username = None, age_group = None, gender = None, name = None, city = None,distro = None, de = None, art = None, about = None, karma = None, promos = None, in_chat = None, joined_last = None, left_last = None, neofetch_last = None, chat_id = None):
    user = update.message.from_user
    chat = update.effective_chat

    if not tg_id:
        tg_id = user.id
    # if not username:
    #     username = user.username

    result = list(sql_upsert_clients(tg_id = tg_id))

    level_text = level_check(result[11], karma)
    if level_text:
        update.message.reply_text(level_text)

    if not karma:
        karma = 0
    if not result[11]:
        result[11] = 0
    if not result[12]:
        result[12] = ''
    karma = karma + result[11]
    if not promos:
        promos = result[12]
    else:
        promos = result[12] + ',' + promos
    result = sql_upsert_clients(tg_id = tg_id, username = username, age_group = age_group , gender = gender , name = name , city = city ,distro = distro , de = de , art = art , about = about , karma = karma, promos = promos , in_chat = in_chat , joined_last = joined_last , left_last = left_last, neofetch_last = neofetch_last, chat_id = chat_id)

    # bot = _.bot
    # bot.send_message(chat_id=-1001514867747,text = str(result))

    return result

def greet_chat_members(update: Update, context: CallbackContext) -> None:
    ###
    # chat_name = 'liberochat'#testing
    chat = update.effective_chat
    logger.info(chat.id)
    ###
    """Greets new users in chats and announces when someone leaves"""
    result = extract_status_change(update.chat_member)
    if result is None:
        return

    was_member, is_member = result
    cause_name = update.chat_member.from_user.mention_html()
    member_name = update.chat_member.new_chat_member.user.mention_html()
    member_username = update.chat_member.new_chat_member.user.username
    user_id = update.chat_member.new_chat_member.user.id
    # logger.info(str(user_id))

    # Idea, filter to only our chat
    # Done, added filter
    if chat.username in CHATS and not was_member and is_member :
        # Idea: add SQL here
        sql_upsert_clients(user_id, username = member_username, in_chat = 1, joined_last = time.time())
        return
    elif chat.username in CHATS and was_member and not is_member :
        sql_upsert_clients(user_id, username = member_username, in_chat = 0, left_last = time.time())
        return

def sql_upsert_clients(tg_id, username = None, age_group = None, gender = None, name = None, city = None,distro = None, de = None, art = None, about = None, karma = None, promos = None, in_chat = None, joined_last = None, left_last = None, neofetch_last = None, chat_id = None):
    arr = [tg_id, username, age_group , gender , name , city ,distro , de , art , about , karma , promos , in_chat , joined_last , left_last , neofetch_last, chat_id]
    db=Database()
    db.execute(f"SELECT * FROM clients WHERE tg_id = {arr[0]}")
    output = db.fetchone()
    if output:
        for i in range(len(arr)):
            if arr[i] == None:
                arr[i] = output[i+1]
        db.executemany(f"""UPDATE clients SET
            username = ?,
            age_group = ?,
            gender = ?,
            name = ?,
            city = ?,
            distro = ?,
            de = ?,
            art = ?,
            about = ?,
            karma = ?,
            promos = ?,
            in_chat = ?,
            joined_last = ?,
            left_last = ?,
            neofetch_last = ?,
            chat_id = ?
            WHERE tg_id = {arr[0]}
        """, arr[1:])
    else:
        db.executemany("""INSERT INTO clients (tg_id, username, age_group, gender, name, city, distro, de, art, about, karma, promos, in_chat, joined_last, left_last, neofetch_last, chat_id )
                       VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""", arr)
    db.execute(f"SELECT * FROM clients WHERE tg_id = {arr[0]}")
    output = db.fetchone()
    db.close()
    return output

def sql_handler_chats(update, _, username = None, group_id = None, group_name = None, group_link = None, group_description = None, added_by_id = None, added_by_username = None, in_chat = None, added_last = None, left_last = None, is_admin = None):
    chat = update.effective_chat
    bot = _.bot

    if not username:
        username = chat.username
    if not group_id:
        group_id = chat.id
    if not group_name:
        group_name = chat.title
    if not group_link and added_last:
        group_link = bot.get_chat(group_id).invite_link
        logger.info(group_link)
    if not group_description and added_last:
        group_description = bot.get_chat(group_id).description
    
    result = sql_upsert_chats(group_id, username = username, group_name = group_name, group_link = group_link, group_description = group_description, added_by_id = added_by_id, added_by_username = added_by_username, in_chat = in_chat, added_last = added_last, left_last = left_last, is_admin = is_admin)

    bot.send_message(chat_id=-1001514867747,text = str(result))

    return result


def sql_upsert_chats(group_id, username = None, group_name = None, group_link = None, group_description = None, added_by_id = None, added_by_username = None, in_chat = None, added_last = None, left_last = None, is_admin = None):
    arr = [group_id, username, group_name, group_link, group_description, added_by_id, added_by_username, in_chat, added_last, left_last, is_admin]

    db=Database()
    db.execute(f"SELECT * FROM chats WHERE group_id = {group_id}")
    output = db.fetchone()
    if output:
        for i in range(len(arr)):
            if arr[i] == None:
                arr[i] = output[i+1]
        db.executemany(f"""UPDATE chats SET
            username = ?,
            group_name = ?,
            group_link = ?,
            group_description = ?,
            added_by_id = ?,
            added_by_username = ?,
            in_chat = ?,
            added_last = ?,
            left_last = ?,
            is_admin = ?
            WHERE group_id = {arr[0]}
        """, arr[1:])
    else:
        db.executemany("""INSERT INTO chats (group_id, username, group_name, group_link, group_description, added_by_id, added_by_username, in_chat, added_last, left_last, is_admin )
                       VALUES (?,?,?,?,?,?,?,?,?,?,?)""", arr)
    db.execute(f"SELECT * FROM chats WHERE group_id = {arr[0]}")
    output = db.fetchone()
    db.close()
    return output


def select_register_good(update: Update, context: CallbackContext) -> None:
    user = update.message.from_user
    chat = update.effective_chat
    if update.message.text.lower() == 'y' or update.message.text.lower() == 'yes' or update.message.text.lower() == 'да':
        update.message.reply_text(
            f'Записано.\nРезультаты можешь посмотреть с помощью "sudo me" или /neofetch в чате.\n Также, ты можешь поменять ASCII картинку в neofetch командой "sudo ascii".',
            reply_markup=ReplyKeyboardMarkup(
                MENU_BUTTONS, one_time_keyboard=True))

        sql_handler(update, context, tg_id = user.id, de = clients[str(user.id)].de, distro = clients[str(user.id)].distro, about = clients[str(user.id)].about)
        clients.pop(str(user.id))
        return END
    elif update.message.text.lower() == 'n' or update.message.text.lower() == 'no' or update.message.text.lower() == 'нет':
        update.message.reply_text(
            f'Ничего не было изменено. Переходим на главную. /help',
            reply_markup=ReplyKeyboardMarkup(
                MENU_BUTTONS, one_time_keyboard=True))
        clients.pop(str(user.id))
        return END
    update.message.reply_text(
        f'y/n или да/нет?',
        reply_markup=ReplyKeyboardMarkup(
            YES_NO_BUTTONS, one_time_keyboard=True))
    return REGISTER_GOOD

def set_karma(update: Update, context: CallbackContext) -> None:
    user = update.message.from_user
    chat = update.effective_chat
    text = update.message.text

    try: 
        karma = int(text[10:])
    except:
        return

    # /setkarma 

    if user.username not in ADMINS:
        return

    if chat.username not in CHATS:
        return

    reply_to_message = update.message.reply_to_message

    if not reply_to_message:
        return

    if reply_to_message.from_user.is_bot:
        return


    target_id = None

    if reply_to_message:
        target_id = reply_to_message.from_user.id

    if not target_id:
        return
    
    output = sql_handler(update, context, tg_id = target_id, karma = karma)
    text = ""
    text +=  'Карма '
    if user.username:
        text+='@'+reply_to_message.from_user.username + " "
    else:
        text += 'пользователя '
    if karma < 0:
        text+= f"опустилось до {output[11]}!"
    else:
        text+= f"поднялась до {output[11]}!"
    update.message.reply_text(f'{text}')


def give_karma(update: Update, context: CallbackContext) -> None:
    user = update.message.from_user
    chat = update.effective_chat
    if chat.username not in CHATS:
        return

    reply_to_message = update.message.reply_to_message
    if not reply_to_message:
        return

    if reply_to_message.from_user.id == user.id:
        update.message.reply_text(f'Самолайкать не положенно!')
        return

    if reply_to_message.from_user.is_bot:
        update.message.reply_text(f'Ботов не трогать!')
        return

    output = sql_handler(update, context, tg_id = reply_to_message.from_user.id, username = reply_to_message.from_user.username, karma = 1)
    text = ""
    text +=  'Карма '
    if user.username:
        text+='@'+reply_to_message.from_user.username + " "
    else:
        text += 'пользователя '
    text+= f"поднялась до {output[11]}!"
    update.message.reply_text(f'{text}')
    return

def extract_status_change(
    chat_member_update: ChatMemberUpdated,
) -> Optional[Tuple[bool, bool]]:
    """Takes a ChatMemberUpdated instance and extracts whether the 'old_chat_member' was a member
    of the chat and whether the 'new_chat_member' is a member of the chat. Returns None, if
    the status didn't change.
    """
    status_change = chat_member_update.difference().get("status")
    old_is_member, new_is_member = chat_member_update.difference().get("is_member", (None, None))

    if status_change is None:
        return None

    old_status, new_status = status_change
    was_member = (
        old_status
        in [
            ChatMember.MEMBER,
            ChatMember.CREATOR,
            ChatMember.ADMINISTRATOR,
        ]
        or (old_status == ChatMember.RESTRICTED and old_is_member is True)
    )
    is_member = (
        new_status
        in [
            ChatMember.MEMBER,
            ChatMember.CREATOR,
            ChatMember.ADMINISTRATOR,
        ]
        or (new_status == ChatMember.RESTRICTED and new_is_member is True)
    )

    return was_member, is_member

def track_chats(update: Update, context: CallbackContext) -> None: #DOESNT ADD TO SQL DB
    """Tracks the chats the bot is in."""
    chat = update.effective_chat
    result = extract_status_change(update.my_chat_member)
    if result is None:
        return
    was_member, is_member = result

    # Let's check who is responsible for the change
    cause_name = update.effective_user.full_name
    cause_username = update.effective_user.full_name
    cause_id = update.effective_user.full_name

    # Handle chat types differently:
    # Idea, add SQL here
    logger.info(f"{chat.id} started the bot")
    if chat.type == Chat.PRIVATE:
        if not was_member and is_member:
            logger.info("%s started the bot", cause_name)
            context.bot_data.setdefault("user_ids", set()).add(chat.id)
        elif was_member and not is_member:
            logger.info("%s blocked the bot", cause_name)
            context.bot_data.setdefault("user_ids", set()).discard(chat.id)
    if chat.type in [Chat.GROUP, Chat.SUPERGROUP]:
        if not was_member and is_member:
            logger.info("%s added the bot to the group %s", cause_name, chat.title)
            sql_handler_chats(update, context, in_chat = 1, added_last = time.time(), added_by_id = cause_id, added_by_username = cause_username)
            context.bot_data.setdefault("group_ids", set()).add(chat.id)
        elif was_member and not is_member:
            logger.info("%s removed the bot from the group %s", cause_name, chat.title)
            sql_handler_chats(update, context, in_chat = 0, left_last = time.time(), added_by_id = cause_id, added_by_username = cause_username)
            context.bot_data.setdefault("group_ids", set()).discard(chat.id)
    else:
        if not was_member and is_member:
            logger.info("%s added the bot to the channel %s", cause_name, chat.title)
            sql_handler_chats(update, context, in_chat = 1, added_last = time.time(), added_by_id = cause_id, added_by_username = cause_username)
            context.bot_data.setdefault("channel_ids", set()).add(chat.id)
        elif was_member and not is_member:
            logger.info("%s removed the bot from the channel %s", cause_name, chat.title)
            sql_handler_chats(update, context, in_chat = 0, left_last = time.time(), added_by_id = cause_id, added_by_username = cause_username)
            context.bot_data.setdefault("channel_ids", set()).discard(chat.id)
    return

def didnt_understand(update: Update, context: CallbackContext) -> None:
    user = update.message.from_user
    chat = update.effective_chat
    update.message.reply_text('Неправилный ввод. /help',
            reply_markup=ReplyKeyboardMarkup(
                MENU_BUTTONS, one_time_keyboard=True))
    return


def select_info(update: Update, context: CallbackContext) -> None:
    user = update.message.from_user
    chat = update.effective_chat
    text = update.message.text[4:].lower()

    names = {}
    for i in list(INFORMATIONS.keys()):
        names.update(INFORMATIONS[i])
    
    desc = ""
    for i in list(INFORMATIONS.keys()):
        desc += i.upper() + ':\n'
        for j in list(INFORMATIONS[i].keys()):
            desc += "   " + j + '\n'
        desc += '\n'

    if not text:
        update.message.reply_text(f"""
man <text> -> поиск статей в нашем Вики
Наш Вики:
{desc}/help""",
            reply_markup=ReplyKeyboardMarkup(
                MENU_BUTTONS, one_time_keyboard=True))

    elif text in names:
        update.message.reply_text(f"""{names[text]}""",
            reply_markup=ReplyKeyboardMarkup(
                MENU_BUTTONS, one_time_keyboard=True))

    else:
        try:
            p = "В базе не нашли, не оно есть в Wiki:\n"
            p += wikipedia.summary(text, sentences=2)
        except wikipedia.DisambiguationError as e:
            try:
                for i in e.options:
                    i = i.lower()
                    if i.lower() != text:
                        p = wikipedia.summary(i, sentences=2)
                        break
            except wikipedia.DisambiguationError:
                p = "Произошла ошибка, просим прощения, у разработчика не из того места руки растут. /help"
            # p = wikipedia.summary(e.options[2])
        except wikipedia.PageError as e:
            p = "Страница не найдена. /help"
        update.message.reply_text( f"""{p}""")
    return

def select_help(update: Update, context: CallbackContext) -> None:
    user = update.message.from_user
    chat = update.effective_chat
    update.message.reply_text( f"""
man <текст> -> узнать информацию о Дистрибутиве, Приложении и тд.
register -> Зарегестрироваться для чата, важно для Neofetch
sudo ascii -> Поставить свой ASCII картинку для Neofetch
me|neofetch|stats -> Вызвать Neofetch
support -> Показать чат для помощи
share -> Поделиться ботом в чатах
promo -> Ввести Промокод
/help -> Вызвать помощника

О Проекте:
about -> О Проекте
privacy -> О Конфедициальности
donate -> Поддержать проект
join -> Учатсвовать в проекте

В чате:
/neofetch или /me -> Вызов Neofetch
Спасибо/Рахмет/Благодарю -> Поблагодарить участника""",
        reply_markup=ReplyKeyboardMarkup(
            MENU_BUTTONS, one_time_keyboard=True))

    return

def select_sudo_handler(update: Update, context: CallbackContext) -> None:
    user = update.message.from_user
    chat = update.effective_chat
    update.message.reply_text('Неправильный аргумент для sudo. /help',
            reply_markup=ReplyKeyboardMarkup(
                MENU_BUTTONS, one_time_keyboard=True))
    return


def select_sudo(update: Update, context: CallbackContext) -> None:
    user = update.message.from_user
    chat = update.effective_chat
    text = update.message.text

    update.message.reply_text(
        f"""Для работы с Sudo требуется аргумент. /help""",
            reply_markup=ReplyKeyboardMarkup(
                MENU_BUTTONS, one_time_keyboard=True))
    return
def select_learn(update: Update, context: CallbackContext) -> None:
    user = update.message.from_user
    chat = update.effective_chat
    url = "https://liberoproject.kz/learn"
    text = "Тема в доработке, может в сайте будет информация"
    keyboard = InlineKeyboardMarkup.from_button(
        InlineKeyboardButton(text="Learn", url=url)
    )
    update.message.reply_text(text, reply_markup=keyboard)
    return

def select_join(update: Update, context: CallbackContext) -> None:
    user = update.message.from_user
    chat = update.effective_chat
    url = "https://liberoproject.kz/join"
    text = f"Вебсайт в доработке, если что пиши лучше в личку. \n @{ADMINS[0]}"
    keyboard = InlineKeyboardMarkup.from_button(
        InlineKeyboardButton(text="Website", url=url)
    )
    update.message.reply_text(text, reply_markup=keyboard)
    return

def select_start(update: Update, context: CallbackContext) -> None:
    user = update.message.from_user
    chat = update.effective_chat
    text = update.message.text
    sql_handler(update, context, tg_id = user.id, username = user.username, chat_id = chat.id)
    update.message.reply_text(
        f"""Добро пожаловать к LiberoBot!\n
            Данный чат является симуляции терминала. Для ознакомления, нажми /help""",
            reply_markup=ReplyKeyboardMarkup(
                MENU_BUTTONS, one_time_keyboard=True))
    return

def select_privacy(update: Update, context: CallbackContext) -> None:
    user = update.message.from_user
    chat = update.effective_chat
    text = update.message.text

    update.message.reply_text(
        f"""Мы собираем данные. Любая программа собирает данные, без них никак нельзя.
Мы собираем:
Ваш telegram id
Ваш username если он есть
Данные которые вы передаете боту, а именно Дистрибутив, Среда Рабочего стола и О Себе
Когда вы вошли в чат и когда вы вышли из чата
Данные всех проведенных опросов также записываются

Эти данные видят лишь авторизованные лица, а именно только создатель канала
Мы не храним целенаправленно данные людей младше 13 лет
База данных передается зашифрованно в Сервера компании Linode.com (скорее всего Германия). Мы перенесем сервера в територию Казахстана как автору не будет лень.

/help""",
            reply_markup=ReplyKeyboardMarkup(
                MENU_BUTTONS, one_time_keyboard=True))
    return

def select_share(update: Update, context: CallbackContext) -> None:
    bot = context.bot
    url = helpers.create_deep_linked_url(bot.username, CHECK_THIS_OUT, group=True)
    text = "Кликни по ссылке чтобы поделиться в чатах!\n"

    update.message.reply_text(text, reply_markup = InlineKeyboardMarkup.from_button(
        InlineKeyboardButton(text="Share", url=url)
    ))
    return

def select_about(update: Update, context: CallbackContext) -> None:
    user = update.message.from_user
    chat = update.effective_chat
    text = update.message.text

    update.message.reply_text(
        f""""Libero Project" основан @{ADMINS[0]} для продвижения Свободного и Открытого ПО в массы.
            Вебсайт: liberoproject.kz
            Instagram: liberoprojectkz
            Youtube: liberoprojectkz

            Телеграм Каналы:
            Канал: @liberoproject
            Чат: @liberochat
            Поддержка: @liberosupport

            Свобода в Цифровом Пространстве.
        /help""",
            reply_markup=ReplyKeyboardMarkup(
                MENU_BUTTONS, one_time_keyboard=True))
    return

def select_not_register(update: Update, context: CallbackContext) -> None:
    user = update.message.from_user
    chat = update.effective_chat

    update.message.reply_text("""Нет доступа. Для получения доступа вам нужно делать через:
'sudo adduser'""",
        reply_markup=ReplyKeyboardMarkup(
            MENU_BUTTONS, one_time_keyboard=True))
    return


def select_donate(update: Update, context: CallbackContext) -> None:
    user = update.message.from_user
    chat = update.effective_chat
    url = "https://liberoproject.kz/donate"
    text = f"""Взнося финансово в проект, вы соглашаетесь с офертой на сайте (пока ее нет, как и самого доната :P)
        А так можете по каспи закинуть, хз, пишите в личку @{ADMINS[0]}"""

    keyboard = InlineKeyboardMarkup.from_button(
        InlineKeyboardButton(text="Donate", url=url)
    )

    update.message.reply_text(text, reply_markup=keyboard)
    return

def select_manadd(update: Update, context: CallbackContext) -> None:
    user = update.message.from_user
    chat = update.effective_chat
    if user.username not in ADMINS:
        return
    text = update.message.text
    num_comma = text.find(',')
    if num_comma == -1:
        update.message.reply_text("Fail, no ','")
        return
    num_n = text.find('\n')
    if num_n == -1:
        update.message.reply_text("Fail, no \\n")
        return

    category = text[8:num_comma]
    
    if text[num_comma+1] == ' ':
        num_comma+=1

    name = text[num_comma+1:num_n]
    content = text[num_n+1:]

    json_upsert(category, name, text = content, mode = "w")

    update.message.reply_text(f"""Added new man
'{category}' - category
'{name}' - name
'{content}'""")
    return

def select_mandel(update: Update, context: CallbackContext) -> None:
    user = update.message.from_user
    chat = update.effective_chat
    if user.username not in ADMINS:
        return
    text = update.message.text

    num_comma = text.find(',')
    if num_comma == -1:
        update.message.reply_text("Fail, no ','")
        return

    category = text[8:num_comma]
    
    if text[num_comma+1] == ' ':
        num_comma+=1

    name = text[num_comma+1:]

    result = json_upsert(category, name, mode = "d")
    if result == 0:
        update.message.reply_text(f"""deleted man
'{category}' - category
'{name}' - name""")
    else:
        update.message.reply_text(f"""ERROR: category {category} with name {name} not found.""")
    return

def select_manshow(update: Update, context: CallbackContext) -> None:
    user = update.message.from_user
    chat = update.effective_chat
    if user.username not in ADMINS:
        return

    update.message.reply_text(pretty(INFORMATIONS, indent=2))
    return

def pretty(d, indent=0):
    total = ''
    for key, value in d.items():
        total += ' ' * indent + str(key) + '\n'
        if isinstance(value, dict):
            total += pretty(value, indent+1) + '\n'
        else:
            total += ' ' * (indent+1) + str(value) + '\n'
    return total

def select_sendall(update: Update, context: CallbackContext) -> None:
    user = update.message.from_user
    chat = update.effective_chat
    if user.username not in ADMINS:
        return
    text = update.message.text

    if text[9:11] != '-y':
        update.message.reply_text("Fail, no -y")
        return
    if len(text.split("\n")) == 1:
        update.message.reply_text("Fail, no -y")
        
    content = '\n'.join(text.split("\n")[1:])
    
    db=Database()
    db.execute(f"SELECT * FROM clients")
    output = db.fetchall()
    db.close()
    
    people = 0
    error = 0
    bot = context.bot
    for i in output:
        try: 
            bot.send_message(chat_id=i[1],text = content)
            people += 1
        except:
            error +=1

    update.message.reply_text(f"""Sent content:
{content}
----------------------
To {people} people
{error} people didnt get the message""")
    return

def select_support_chat(update: Update, context: CallbackContext) -> None:
    user = update.message.from_user
    chat = update.effective_chat
    url = "https://t.me/liberosupport"
    text = "В сообществе вам ответят на ваши вопросы"
    keyboard = InlineKeyboardMarkup.from_button(
        InlineKeyboardButton(text="В Чат", url=url)
    )
    update.message.reply_text(text, reply_markup=keyboard)
    return

def deep_linked_level_1(update: Update, context: CallbackContext) -> None:
    """Reached through the CHECK_THIS_OUT payload"""
    bot = context.bot
    url = helpers.create_deep_linked_url(bot.username, GOT_BY_LINK)

    keyboard = [
        [
            InlineKeyboardButton("Канал", url='https://t.me/liberoproject'),
            InlineKeyboardButton("Чат", url='https://t.me/liberochat'),
        ],
        [InlineKeyboardButton("К Боту", url=url)],
    ]

    text = (
        """Всем привет!
Мы создаем контент про Свободное ПО
Если тебя интересует:
    Обучение Linux;
    Уютный Чат;
    или Мемасики
То ждем тебя на нашем канале!"""
    )

    update.message.reply_text(text, reply_markup=InlineKeyboardMarkup(keyboard))
    return

def deep_linked_level_2(update: Update, context: CallbackContext) -> None:
    """Reached through the SO_COOL payload"""
    user = update.message.from_user
    chat = update.effective_chat
    sql_handler(update, context, tg_id = user.id, username = user.username, chat_id = chat.id)
    update.message.reply_text(
        f"""Добро пожаловать к LiberoBot!\n
            Данный чат является симуляции терминала. Для ознакомления, нажми /help
            """,
            reply_markup=ReplyKeyboardMarkup(
                MENU_BUTTONS, one_time_keyboard=True))

def select_neofetch_chat(update: Update, context: CallbackContext) -> None:
    """Reached through the SO_COOL payload"""
    user = update.message.from_user
    chat = update.effective_chat

    info = sql_handler(update, context)
    if info[16]:
        if time.time() - info[16] < 300:
            update.message.reply_text("Neofetch можно вызывать лишь раз 5 минут!")
            return

    karma = info[11]
    if not karma:
        karma = 0

    if karma<LEVELS[0][1]:
        update.message.reply_text("""
У тебя недостаточно кармы. Можешь его получить помогая другим, или смотря наши видео и вводя промокоды. Пиши мне в личку за подробностями
        """)
        return

    select_neofetch(update, context)
    sql_handler(update, context, neofetch_last = time.time())

def json_upsert(category, name, text = "default", mode = 'r'): # mode = d-delete, r-read, w-upsert
    if category not in list(INFORMATIONS.keys()):
        INFORMATIONS[category] = {}

    if mode == "w":
        INFORMATIONS[category][name] = text

    elif mode == "d":
        try:
            del INFORMATIONS[category][name]
            if len(INFORMATIONS[category]) == 0:
                del INFORMATIONS[category]
        except:
            return -1
    else:
        return 1

    with open('info.json', 'w', encoding='utf-8') as f:
        json.dump(INFORMATIONS, f, ensure_ascii=False, indent=4)

    return 0

def select_neofetch(update: Update, context: CallbackContext) -> None:
    """Reached through the SO_COOL payload"""
    user = update.message.from_user
    chat = update.effective_chat

    info = sql_handler(update, context)

    art = """        _nnnn_
        dGGGGMMb
       @l~ib~~ero
       M|@||@) M|
       @,----.JM|
      JS^\__/  qKL
     dZP        qKRb
    dZP          qKKb
   fZP            SMMb
   HZM            MMMM
   FqM            MMMM
 __| ".        |\dS"qML
 |    `.       | `' \Zq
_)      \.___.,|     .'
\____   )MMMMMP|   .'
     `-'       `--' """
    if info[9]:
        if info[9] != "default":
            art = info[9]

    about = info[10]
    os = info[7]
    de = info[8]
    username = info[2]

    karma = info[11]
    if not karma:
        karma = 0

    if karma<LEVELS[1][1]:
        art = ""

    level = find_level(karma)

    if not username:
        username = str(info[1])

    username += "@liberoproject"
    if not about:
        about = 'No info...'
    if not de:
        de = 'No info...'
    if not about:
        about = 'ABOUT: No info...'
    else:
        about = 'ABOUT:' + about
        chunks, chunk_size = len(about), 25
        about = '\n'.join([ about[i:i+chunk_size] for i in range(0, chunks, chunk_size) ])
    info_text = f"""{username}
OS: {os}
DE: {de}
LEVEL: {level[0]}
KARMA: {karma}
{about}
"""
    update.message.reply_text(
        f"""```{art}
-------------------------
{info_text}```""", parse_mode = "Markdown")

def main() -> None:
    updater = Updater(TOKEN) # liberobot
    dispatcher = updater.dispatcher

    registration_handler = ConversationHandler(
        entry_points=[
            MessageHandler(Filters.regex('^([Ss]udo)\ (adduser).*') & Filters.chat_type.private, select_register)],
        states={
            REGISTER_DISTRO : [MessageHandler(Filters.text, select_register_distro)],
            REGISTER_DE : [MessageHandler(Filters.text, select_register_de)],
            REGISTER_ABOUT : [MessageHandler(Filters.text, select_register_about)],
            REGISTER_GOOD : [MessageHandler(Filters.text, select_register_good)],
        },
        fallbacks=[
            CommandHandler('stop', stop_nested),
        ],
        map_to_parent={
            # End conversation altogether
            STOPPING: STOPPING,
        },
    )

    ascii_handler = ConversationHandler(
        entry_points=[MessageHandler(Filters.regex('^([sS]udo)\ (ascii).*') & Filters.chat_type.private, select_ascii)],
        states={
            ASCII_INPUT : [MessageHandler(Filters.text, select_ascii_input)],
            ASCII_GOOD : [MessageHandler(Filters.text, select_ascii_good)]
        },
        fallbacks=[
            CommandHandler('stop', stop_nested),
        ],
        map_to_parent={
            # End conversation altogether
            STOPPING: STOPPING,
        },
    )

    chat_auto_handlers = [
        ChatMemberHandler(track_chats, ChatMemberHandler.MY_CHAT_MEMBER),
        ChatMemberHandler(greet_chat_members, ChatMemberHandler.CHAT_MEMBER)
    ]

    chat_handlers = [
        CommandHandler('setkarma', set_karma, Filters.chat_type.groups), # /info <distro>
        # MessageHandler(Filters.regex('^([Ss]udo\ setkarma).*'), set_karma, Filters.chat_type.groups), # /info <distro>
        CommandHandler('neofetch', select_neofetch_chat, Filters.chat_type.groups), # /info <distro>
        CommandHandler('me', select_neofetch_chat, Filters.chat_type.groups), # /info <distro>
        MessageHandler(Filters.regex('.*([сС]пасибо|[Пп]асеба|[рР]ахмет|[бБ]лагодарю|[оО]т\ души|[👍❤️🙏]|[tT]hanks|[tT]hank you|[рР]аха).*') & Filters.chat_type.groups, give_karma) #Карма
    ]

    private_handlers = [
        CommandHandler('help', select_help, Filters.chat_type.private), # /info <distro>
        CommandHandler("start", deep_linked_level_2, Filters.regex(GOT_BY_LINK)),
        CommandHandler("start", deep_linked_level_1, Filters.regex(CHECK_THIS_OUT)),
        CommandHandler("start", select_start, Filters.chat_type.private),
        CommandHandler('me', select_neofetch, Filters.chat_type.private), # /info <distro>
        CommandHandler('neofetch', select_neofetch, Filters.chat_type.private), # /info <distro>

        MessageHandler(Filters.regex('^([Рр]егистрация).*') & Filters.chat_type.private, select_not_register), #about

        MessageHandler(Filters.regex('^(О\ Проекте|[Aa]bout).*') & Filters.chat_type.private, select_about), #about
        # MessageHandler(Filters.regex('^([Пп]оддержка|[Ss]upport).*') & Filters.chat_type.private, select_support_chat), #Техподдержка
        MessageHandler(Filters.regex('^(Поделиться|[Ss]hare).*') & Filters.chat_type.private, select_share),
        MessageHandler(Filters.regex('^(Приватность|[Pp]rivacy).*') & Filters.chat_type.private, select_privacy),
        MessageHandler(Filters.regex('^(Поддержать|[Dd]onate).*') & Filters.chat_type.private, select_donate),
        MessageHandler(Filters.regex('^(Участвовать|[Jj]oin).*') & Filters.chat_type.private, select_join),
        # Не будет рук создавать этот сегмент 
        # MessageHandler(Filters.regex('^(Учиться|[Ll]earn).*') & Filters.chat_type.private, select_learn),
        MessageHandler(Filters.regex('^(Вики|[Mm]an).*') & Filters.chat_type.private, select_info),
        MessageHandler(Filters.regex('^(Промокоды|[Pp]romo).*') & Filters.chat_type.private, select_promo),
            ]

    sudo_handlers = [
        MessageHandler(Filters.regex('^([sS]udo)$') & Filters.chat_type.private, select_sudo), # sudo <something>
        # MessageHandler(Filters.regex('^([sS]udo)\ (about).*') & Filters.chat_type.private, select_about), #about
        # MessageHandler(Filters.regex('^([sS]udo)\ (support).*') & Filters.chat_type.private, select_support_chat), #Техподдержка
        # MessageHandler(Filters.regex('^([sS]udo)\ (share).*') & Filters.chat_type.private, select_share),
        # MessageHandler(Filters.regex('^([sS]udo)\ (privacy).*') & Filters.chat_type.private, select_privacy),
        # MessageHandler(Filters.regex('^([sS]udo)\ (donate).*') & Filters.chat_type.private, select_donate),
        # MessageHandler(Filters.regex('^([sS]udo)\ (join).*') & Filters.chat_type.private, select_join),
        # MessageHandler(Filters.regex('^([sS]udo)\ (learn).*') & Filters.chat_type.private, select_learn),
        # MessageHandler(Filters.regex('^([sS]udo)\ (info).*') & Filters.chat_type.private, select_info),
        # MessageHandler(Filters.regex('^([sS]udo)\ (promo).*') & Filters.chat_type.private, select_promo),
        ascii_handler,
        registration_handler, # + sudo handlers
        MessageHandler(Filters.regex('^([sS]udo)\ (neofetch|stats|me).*') & Filters.chat_type.private, select_neofetch),
        # Не имеет смысла это создавать
        # MessageHandler(Filters.regex('^([sS]udo)\ response*') & Filters.chat_type.private, select_response),
        MessageHandler(Filters.regex('^([sS]udo)\ *') & Filters.chat_type.private, select_sudo_handler),
    ]

    default_one = MessageHandler(Filters.all & Filters.chat_type.private, didnt_understand)

    admin_handlers = [
        # MessageHandler(Filters.regex('^(Перейти к чату)$') & Filters.chat_type.private, select_promo), # Посмотреть базы даннных
        CommandHandler('manadd', select_manadd, Filters.chat_type.private), # /info <distro>
        CommandHandler('mandel', select_mandel, Filters.chat_type.private), # /info <distro>
        CommandHandler('manshow', select_manshow, Filters.chat_type.private), # /info <distro>
        CommandHandler('sendall', select_sendall, Filters.chat_type.private), # /info <distro>
    ]

    # Additional functionality
    # send message of db updates to log channel

    # dispatcher code
    for i in admin_handlers:
       dispatcher.add_handler(i)
    for i in chat_handlers:
       dispatcher.add_handler(i)
    for i in chat_auto_handlers:
       dispatcher.add_handler(i)
    for i in private_handlers:
        dispatcher.add_handler(i)
    for i in sudo_handlers:
        dispatcher.add_handler(i)
    dispatcher.add_handler(default_one)

    updater.start_polling(allowed_updates=Update.ALL_TYPES)
    updater.idle()

# get tokens
with open (TOKEN_FILE, "r") as myfile:
    # FUCK YOU HACKEERS
    TOKEN=myfile.readline().replace('\n', '')
    CHATS = json.loads(myfile.readline().replace('\n', ''))
    ADMINS = json.loads(myfile.readline().replace('\n', ''))

# parse json file for config
with open('info.json', 'r') as myfile:
    data=myfile.read()
    obj = json.loads(data)
INFORMATIONS = obj

INFORMATIONS = obj
with open('levels.json', 'r') as myfile:
    data=myfile.read()
    obj = json.loads(data)
LEVELS = obj

with open('promos.json', 'r') as myfile:
    data=myfile.read()
    obj = json.loads(data)
PROMOS = obj

if __name__ == '__main__':
    # create a db if none
    db = Database()
    db.create_table()
    db.close()

    main()

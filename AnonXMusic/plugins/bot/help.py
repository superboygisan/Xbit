import random
import aiohttp
from typing import Union

from pyrogram import filters, types
from pyrogram.types import InlineKeyboardMarkup, Message, InlineKeyboardButton, CallbackQuery
from pyrogram.errors import MessageNotModified
from pyrogram.enums import ParseMode

from AnonXMusic import app
from AnonXMusic.misc import SUDOERS
from AnonXMusic.utils import help_pannel
from AnonXMusic.utils.database import (
    get_lang,
    get_model_settings,
    update_model_settings
)
from AnonXMusic.utils.decorators.language import LanguageStart, languageCB
from AnonXMusic.utils.inline.help import help_back_markup, private_help_panel

from config import (
    BANNED_USERS,
    START_IMG_URL,
    SUPPORT_CHAT,
    SHRUTI_API_URL,
)

import config
from strings import get_string, helpers


# -------------------- FETCHERS -------------------- #

async def fetch_tts_models():
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(
                f"{SHRUTI_API_URL}/tts/models"
            ) as response:

                if response.status == 200:
                    data = await response.json()
                    return data.get("speakers", [])

                return []

    except Exception as e:
        print(f"TTS Error: {e}")
        return []


async def fetch_image_models():
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(
                f"{SHRUTI_API_URL}/image/models"
            ) as response:

                if response.status == 200:
                    data = await response.json()
                    return data.get("models", [])

                return []

    except Exception as e:
        print(f"Image Error: {e}")
        return []


async def fetch_ai_models():
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(
                f"{SHRUTI_API_URL}/ai/models"
            ) as response:

                if response.status == 200:
                    data = await response.json()
                    return data.get("models", [])

                return []

    except Exception as e:
        print(f"AI Error: {e}")
        return []


# -------------------- HELP -------------------- #

@app.on_message(filters.command(["help"]) & filters.private & ~BANNED_USERS)
@app.on_callback_query(filters.regex("settings_back_helper") & ~BANNED_USERS)
async def helper_private(
    client,
    update: Union[types.Message, types.CallbackQuery]
):

    is_callback = isinstance(update, types.CallbackQuery)
    is_sudo = update.from_user.id in SUDOERS

    if is_callback:

        try:
            await update.answer()
        except:
            pass

        chat_id = update.message.chat.id
        language = await get_lang(chat_id)
        _ = get_string(language)

        keyboard = help_pannel(_, is_sudo, True)

        await update.edit_message_text(
            _["help_1"].format(SUPPORT_CHAT),
            reply_markup=keyboard
        )

    else:

        try:
            await update.delete()
        except:
            pass

        language = await get_lang(update.chat.id)
        _ = get_string(language)

        keyboard = help_pannel(_, is_sudo)

        await update.reply_photo(
            photo=random.choice(config.START_IMG_URL),
            caption=_["help_1"].format(SUPPORT_CHAT),
            reply_markup=keyboard,
        )


@app.on_message(filters.command(["help"]) & filters.group & ~BANNED_USERS)
@LanguageStart
async def help_com_group(client, message: Message, _):

    keyboard = private_help_panel(_)

    await message.reply_text(
        _["help_2"],
        reply_markup=InlineKeyboardMarkup(keyboard)
    )


# -------------------- CALLBACKS -------------------- #

@app.on_callback_query(filters.regex("help_callback") & ~BANNED_USERS)
@languageCB
async def helper_cb(client, CallbackQuery: CallbackQuery, _):

    callback_data = CallbackQuery.data.strip()
    cb = callback_data.split(None, 1)[1]

    keyboard = help_back_markup(_)

    if cb == "hb16":

        btn = [
            [
                InlineKeyboardButton(
                    text="🤖 AI Model Setting",
                    callback_data="help_callback hb19",
                )
            ],
            [
                InlineKeyboardButton(
                    text="🎤 TTS Model Setting",
                    callback_data="help_callback hb17",
                )
            ],
            [
                InlineKeyboardButton(
                    text="🎨 IMAGE Model Setting",
                    callback_data="help_callback hb18",
                )
            ],
            [
                InlineKeyboardButton(
                    text=_["BACK_BUTTON"],
                    callback_data="settings_back_helper",
                )
            ]
        ]

        await CallbackQuery.edit_message_text(
            f"⚡ AI, TTS and Image Model Settings\n\n"
            f"[Check Docs here]({SHRUTI_API_URL}/docs)",
            reply_markup=InlineKeyboardMarkup(btn),
            parse_mode=ParseMode.MARKDOWN
        )

    elif cb == "hb17":

        model_settings = await get_model_settings()
        current_tts = model_settings.get("tts", "athena")

        speakers = await fetch_tts_models()

        if not speakers:

            try:
                await CallbackQuery.edit_message_text(
                    "❌ Unable to fetch TTS models.",
                    reply_markup=InlineKeyboardMarkup(
                        [[
                            InlineKeyboardButton(
                                text=_["BACK_BUTTON"],
                                callback_data="help_callback hb16"
                            )
                        ]]
                    )
                )
            except MessageNotModified:
                pass

            return

        buttons = []
        row = []

        for speaker in speakers:

            speaker_id = speaker["speaker"]
            name = speaker["name"]

            text = (
                f"✅ {name}"
                if speaker_id == current_tts
                else name
            )

            row.append(
                InlineKeyboardButton(
                    text=text,
                    callback_data=f"tts_model_{speaker_id}"
                )
            )

            if len(row) == 2:
                buttons.append(row)
                row = []

        if row:
            buttons.append(row)

        buttons.append(
            [
                InlineKeyboardButton(
                    text=_["BACK_BUTTON"],
                    callback_data="help_callback hb16"
                )
            ]
        )

        try:
            await CallbackQuery.edit_message_text(
                "🎤 **TTS Model Settings**\n\n"
                "Select a voice model",
                reply_markup=InlineKeyboardMarkup(buttons),
                parse_mode=ParseMode.MARKDOWN
            )

        except MessageNotModified:
            pass


# -------------------- TTS SELECT -------------------- #

@app.on_callback_query(filters.regex(r"tts_model_") & ~BANNED_USERS)
@languageCB
async def tts_model_callback(
    client,
    CallbackQuery: CallbackQuery,
    _
):

    try:
        await CallbackQuery.answer()
    except:
        pass

    model_name = CallbackQuery.data.replace(
        "tts_model_",
        ""
    )

    success = await update_model_settings(
        {"tts": model_name}
    )

    if success:

        await CallbackQuery.edit_message_text(
            f"✅ TTS Model Updated\n\n"
            f"Current Model: `{model_name}`",
            parse_mode=ParseMode.MARKDOWN
        )

    else:

        await CallbackQuery.edit_message_text(
            "❌ Failed To Update TTS Model"
        )
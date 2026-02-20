import tempfile

from telegram import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    Update,
)
from telegram.ext import (
    Application,
    CallbackContext,
    CallbackQueryHandler,
    CommandHandler,
    MessageHandler,
    filters,
)

from agents.agent_controllers import LlmController
from config import settings
from db_connector import DatabaseConnector
import logging
    

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

db_connector = DatabaseConnector()
user_models: dict[int, str] = {}


def get_user_llm_controller(user_id: int) -> LlmController:
    """Get or create LlmController for a specific user with their model preference."""
    model = user_models.get(user_id, settings.DEFAULT_MODEL)
    return LlmController(model_name=model)


async def model_command(update: Update) -> None:
    """Handle /model command to show model selection menu."""
    keyboard: list[list[InlineKeyboardButton]] = []

    keyboard.append(
        [InlineKeyboardButton("OpenAI Models", callback_data="group_openai")]
    )
    for model in settings.OPENAI_MODELS_LIST:
        display_name = model.replace("gpt-", "").replace("-", " ").title()
        keyboard.append(
            [InlineKeyboardButton(f"• {display_name}", callback_data=f"model_{model}")]
        )

    keyboard.append([InlineKeyboardButton("━━━━━━━━━━━━", callback_data="separator")])

    keyboard.append(
        [InlineKeyboardButton("Together AI Models", callback_data="group_together")]
    )
    for model in settings.TOGETHER_MODELS_LIST:
        display_name = model.split("/")[-1].replace("-", " ").title()
        if len(display_name) > 30:
            display_name = display_name[:27] + "..."

        keyboard.append(  # pyright: ignore[reportUnknownMemberType]
            [InlineKeyboardButton(f"• {display_name}", callback_data=f"model_{model}")]
        )

    reply_markup = InlineKeyboardMarkup(keyboard)  # pyright: ignore[reportUnknownArgumentType]

    current_model = user_models.get(update.effective_user.id, settings.DEFAULT_MODEL)
    await update.message.reply_text(
        f"Select a model:\n\nCurrent: <b>{current_model}</b>",
        reply_markup=reply_markup,
        parse_mode="HTML",
    )


async def model_callback(update: Update) -> None:
    """Handle model selection button callbacks."""
    query = update.callback_query
    await query.answer()

    if query.data.startswith("model_"):
        model_name = query.data.replace("model_", "")
        user_id = update.effective_user.id
        user_models[user_id] = model_name

        await query.edit_message_text(
            f"Model changed to: <b>{model_name}</b>", parse_mode="HTML"
        )

    elif query.data in ("group_openai", "group_together", "separator"):
        await query.answer()


async def response_all(update: Update, context: CallbackContext) -> None:
    """Handles all messages that are not commands."""
    user_id = update.message.from_user.id  # type: ignore telegram library does not properly annotate this
    username = update.message.from_user.username  # type: ignore telegram library does not properly annotate this
    llm_controller = get_user_llm_controller(user_id)

    if update.message.text:  # type: ignore
        text = update.message.text  # type: ignore

    elif update.message.voice:  # type: ignore
        voice = update.message.voice  # type: ignore
        file_id = voice.file_id

        file = await context.bot.get_file(file_id)  # type: ignore
        temp_path = tempfile.NamedTemporaryFile(delete=False, suffix=".ogg").name
        await file.download_to_drive(temp_path)  # type: ignore

        text = llm_controller.transcribe_text(temp_path)

    curr_type = await llm_controller.classify_text(text)  # type: ignore also tg

    if curr_type in ("dream", "thought", "plans"):
        db_connector.add_thought(user_id, username, text, curr_type)  # type: ignore
        logger.info(f"Added {curr_type} for user {username} (ID: {user_id}) to the database.")

        my_response = (
            f"{curr_type.upper()} with content: {text} from {username} added to DB"  # type: ignore
        )

        await context.bot.send_message(  # type: ignore also tg
            chat_id=update.effective_chat.id,
            text=my_response,
            parse_mode="HTML",  # type: ignore I'm giving up on all the telegram lib typing errors
        )

    elif curr_type == "retreive":
        max_retries = 3
        my_query: str | None = None
        my_response = None

        for attempt in range(max_retries):
            my_query = await llm_controller.generate_sql_query(text, username, user_id)
            my_response = db_connector.execute_custom_query(my_query, user_id, username)
            logger.info(f"Custom query attempt {attempt + 1}: {my_query} with response: {my_response}")

            if my_response is not None:
                break
            elif attempt < max_retries - 1:
                text = (
                    f"{text} IMPORTANT: The query MUST include 'user_tg_id = {user_id}' in "
                    f"the WHERE clause to filter by the correct user."
                )

        if my_response:
            for thought in my_response:
                logger.info(f"Retrieved thought of user {username} (ID: {user_id}): {thought}")
                await context.bot.send_message(
                    chat_id=update.effective_chat.id, text=thought, parse_mode="HTML"
                )
        else:
            await context.bot.send_message(
                chat_id=update.effective_chat.id,
                text="Unable to generate a secure query. Please try again with a more specific request.",
                parse_mode="HTML",
            )

    elif curr_type == "analyze":
        max_retries = 3
        my_query: str | None = None
        retreived_analisys: list[str] | None = None

        for attempt in range(max_retries):
            my_query = await llm_controller.generate_sql_query(text, username, user_id)
            retreived_analisys = db_connector.execute_custom_query(
                my_query, user_id, username
            )
            logger.info(f"Analysis query attempt {attempt + 1}: {my_query} with response: {retreived_analisys}")

            if retreived_analisys is not None:
                break
            elif attempt < max_retries - 1:
                text = (
                    f"{text} IMPORTANT: The query MUST include 'user_tg_id = {user_id}' in "
                    f"the WHERE clause to filter by the correct user."
                )

        if retreived_analisys:
            all_together = " ### NEXT DREAM: ###".join(retreived_analisys)

            my_response = await llm_controller.analyze_dreams_or_thoughts(all_together)

            await context.bot.send_message(
                chat_id=update.effective_chat.id, text=my_response, parse_mode="HTML"
            )
        else:
            await context.bot.send_message(
                chat_id=update.effective_chat.id,
                text="Unable to generate a secure query for analysis. Please try again with a more specific request.",
                parse_mode="HTML",
            )


response_all_handler = MessageHandler(  # type: ignore
    (filters.TEXT | filters.VOICE) & (~filters.COMMAND), response_all
)
model_command_handler = CommandHandler("model", model_command)
model_callback_handler = CallbackQueryHandler(
    model_callback, pattern="^(model_|group_|separator)"
)

print("Building app")
application = Application.builder().token(settings.BOT_KEY).build()

application.add_handler(model_command_handler)
application.add_handler(model_callback_handler)
application.add_handler(response_all_handler)
print("Building is done")



if __name__ == "__main__":
    application.run_polling()
# ELECT * FROM thoughts WHERE username = 'dima_in_the_forest' AND type =
# 'dream' AND datetime BETWEEN '2026-02-20 23:10:48' AND '2026-02-20 23:40:48' ORDER BY datetime DESC"

# SELECT * FROM thoughts WHERE username = 'dima_in_the_forest' AND type = 'dream' AND datetime 
# BETWEEN '2026-02-20 20:40:11' AND '2026-02-20 23:40:11' ORDER BY datetime DESC
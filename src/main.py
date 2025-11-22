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

from agents import (
    DEFAULT_MODEL,
    LlmController,
    OPENAI_MODELS_LIST,
    TOGETHER_MODELS_LIST,
)
from config import settings
from db_connector import DatabaseConnector


db_connector = DatabaseConnector()
# Store user model preferences: {user_id: model_name}
user_models: dict[int, str] = {}


def get_user_llm_controller(user_id: int) -> LlmController:
    """Get or create LlmController for a specific user with their model preference."""
    model = user_models.get(user_id, DEFAULT_MODEL)
    return LlmController(model_name=model)


async def model_command(update: Update, context: CallbackContext) -> None:
    """Handle /model command to show model selection menu."""
    keyboard = []
    
    # Add OpenAI models
    keyboard.append([InlineKeyboardButton("🤖 OpenAI Models", callback_data="group_openai")])
    for model in OPENAI_MODELS_LIST[:4]:  # Show first 4 OpenAI models
        display_name = model.replace("gpt-", "").replace("-", " ").title()
        keyboard.append([InlineKeyboardButton(
            f"• {display_name}",
            callback_data=f"model_{model}"
        )])
    
    # Add separator
    keyboard.append([InlineKeyboardButton("━━━━━━━━━━━━", callback_data="separator")])
    
    # Add Together AI models
    keyboard.append([InlineKeyboardButton("🔮 Together AI Models", callback_data="group_together")])
    for model in TOGETHER_MODELS_LIST[:6]:  # Show first 6 Together models
        # Shorten model names for display
        display_name = model.split("/")[-1].replace("-", " ").title()
        if len(display_name) > 30:
            display_name = display_name[:27] + "..."
        keyboard.append([InlineKeyboardButton(
            f"• {display_name}",
            callback_data=f"model_{model}"
        )])
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    current_model = user_models.get(update.effective_user.id, DEFAULT_MODEL)
    await update.message.reply_text(
        f"Select a model:\n\nCurrent: <b>{current_model}</b>",
        reply_markup=reply_markup,
        parse_mode="HTML"
    )


async def model_callback(update: Update, context: CallbackContext) -> None:
    """Handle model selection button callbacks."""
    query = update.callback_query
    await query.answer()
    
    if query.data.startswith("model_"):
        model_name = query.data.replace("model_", "")
        user_id = update.effective_user.id
        user_models[user_id] = model_name
        
        await query.edit_message_text(
            f"✅ Model changed to: <b>{model_name}</b>",
            parse_mode="HTML"
        )
    elif query.data in ("group_openai", "group_together", "separator"):
        # Ignore group headers and separators
        await query.answer()


async def response_all(update: Update, context: CallbackContext) -> None:
    """Handles all messages that are not commands."""
    user_id = update.message.from_user.id
    username = update.message.from_user.username
    llm_controller = get_user_llm_controller(user_id)

    if update.message.text:
        text = update.message.text

    elif update.message.voice:
        voice = update.message.voice
        file_id = voice.file_id

        file = await context.bot.get_file(file_id)
        temp_path = tempfile.NamedTemporaryFile(delete=False, suffix=".ogg").name
        await file.download_to_drive(temp_path)

        text = llm_controller.transcribe_text(temp_path)

    # Classify the message using the AI agent
    curr_type = await llm_controller.classify_text(text)

    if curr_type in ("dream", "thought", "plans"):
        db_connector.add_thought(user_id, username, text, curr_type)
        my_response = (
            f"{curr_type.upper()} with content: {text} from {username} added to DB"
        )

        await context.bot.send_message(
            chat_id=update.effective_chat.id, text=my_response, parse_mode="HTML"
        )

    elif curr_type == "retreive":
        # Generate SQL query using the AI agent with retry on validation failure
        max_retries = 3
        my_query = None
        my_response = None
        
        for attempt in range(max_retries):
            my_query = await llm_controller.generate_sql_query(text, username, user_id)
            my_response = db_connector.execute_custom_query(my_query, user_id, username)
            
            if my_response is not None:
                # Query passed validation, break out of retry loop
                break
            elif attempt < max_retries - 1:
                # Reprompt with emphasis on user_tg_id requirement
                text = f"{text} IMPORTANT: The query MUST include 'user_tg_id = {user_id}' in the WHERE clause to filter by the correct user."
        
        if my_response:
            for thought in my_response:
                await context.bot.send_message(
                    chat_id=update.effective_chat.id, text=thought, parse_mode="HTML"
                )
        else:
            await context.bot.send_message(
                chat_id=update.effective_chat.id,
                text="❌ Unable to generate a secure query. Please try again with a more specific request.",
                parse_mode="HTML"
            )

    elif curr_type == "analyze":
        # Generate SQL query to retrieve data for analysis with retry on validation failure
        max_retries = 3
        my_query = None
        retreived_stuff = None
        
        for attempt in range(max_retries):
            my_query = await llm_controller.generate_sql_query(text, username, user_id)
            retreived_stuff = db_connector.execute_custom_query(my_query, user_id, username)
            
            if retreived_stuff is not None:
                # Query passed validation, break out of retry loop
                break
            elif attempt < max_retries - 1:
                # Reprompt with emphasis on user_tg_id requirement
                text = f"{text} IMPORTANT: The query MUST include 'user_tg_id = {user_id}' in the WHERE clause to filter by the correct user."
        
        if retreived_stuff:
            all_together = " ### NEXT DREAM: ###".join(retreived_stuff)
            
            # Analyze using the AI agent (handles chunking and summarization internally if needed)
            my_response = await llm_controller.analyze_dreams_or_thoughts(all_together)

            await context.bot.send_message(
                chat_id=update.effective_chat.id, text=my_response, parse_mode="HTML"
            )
        else:
            await context.bot.send_message(
                chat_id=update.effective_chat.id,
                text="❌ Unable to generate a secure query for analysis. Please try again with a more specific request.",
                parse_mode="HTML"
            )


response_all_handler = MessageHandler(
    (filters.TEXT | filters.VOICE) & (~filters.COMMAND), response_all
)
model_command_handler = CommandHandler("model", model_command)
model_callback_handler = CallbackQueryHandler(model_callback, pattern="^(model_|group_|separator)")

print("Building app")
application = Application.builder().token(settings.BOT_KEY).build()

application.add_handler(model_command_handler)
application.add_handler(model_callback_handler)
application.add_handler(response_all_handler)
print("Building is done")


if __name__ == "__main__":
    application.run_polling()

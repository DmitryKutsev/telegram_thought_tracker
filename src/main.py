import os
import asyncio
import tempfile


from dotenv import load_dotenv
from telegram import (
    Bot,
    ReplyKeyboardRemove,
    Update,
)
from telegram.ext import (
    Updater,
    Application,
    ContextTypes,
    CallbackContext,
    ConversationHandler,
    MessageHandler,
    filters,
)


from db_connector import DatabaseConnector
from llm_pipeline import LlmController

load_dotenv()

BOT_KEY = os.getenv("BOT_KEY")
PORT = int(os.getenv("PORT", "5000"))
APP_NAME = os.getenv("APP_NAME", "glacial-caverns-10538")
WEBHOOK_LINK = os.getenv("WEBHOOK_LINK")


db_connector = DatabaseConnector()


DEFAULT_MODEL = "gpt-4o"

# curr_dir = Path(__file__).parent

TOGETHER_MODELS_LIST = [
    "meta-llama/Llama-3.3-70B-Instruct-Turbo",
    "Qwen/QwQ-32B-Preview",
    "meta-llama/Llama-3-70b-chat-hf",
    "mistralai/Mixtral-8x22B-Instruct-v0.1",
    "Qwen/Qwen1.5-110B-Chat",
    "WizardLM/WizardLM-13B-V1.2",
    "togethercomputer/RedPajama-INCITE-7B-Chat",
    "togethercomputer/alpaca-7b",
]

ALL_MODELS_LIST = TOGETHER_MODELS_LIST + [DEFAULT_MODEL]
MODELS_IN_USE_LIST = [DEFAULT_MODEL]

last_msg_lst = [" "]


async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Cancels and ends the conversation."""
    await update.message.reply_text(
        "Bye! Hope to talk to you again soon.", reply_markup=ReplyKeyboardRemove()
    )
    return ConversationHandler.END


async def response_all(update: Update, context: CallbackContext) -> None:
    """Handles all messages that are not commands."""
    llm_controller = LlmController()
    user_id = update.message.from_user.id
    username = update.message.from_user.username

    if update.message.text:
        text = update.message.text

    elif update.message.voice:
        voice = update.message.voice
        file_id = voice.file_id

        file = await context.bot.get_file(file_id)
        temp_path = tempfile.NamedTemporaryFile(delete=False, suffix=".ogg").name
        await file.download_to_drive(temp_path)

        text = llm_controller.transcribe_text(temp_path)

    last_msg_lst[0] = text
    curr_type = llm_controller.classify_text(text)

    db_connector.add_thought(user_id, username, text, curr_type)
    my_response = (
        f"{curr_type.upper()} with content: {text} from {username} added to DB"
    )
    print(my_response)

    await context.bot.send_message(
        chat_id=update.effective_chat.id, text=my_response, parse_mode="HTML"
    )


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send a message when the command /start is issued."""
    user = update.effective_user
    await update.message.reply_text(
        rf"Hi {user.mention_html()}!",
        parse_mode="HTML",
        reply_markup=ReplyKeyboardRemove(),
    )


def run() -> None:
    """Run the bot."""
    print("starting app")

    application.run_webhook(
        listen="0.0.0.0",
        port=PORT,
        url_path=BOT_KEY,
        webhook_url=f"{WEBHOOK_LINK}/{BOT_KEY}",
    )


my_bot = Bot(token=BOT_KEY)
my_queue = asyncio.Queue()

updater = Updater(my_bot, my_queue)

response_all_handler = MessageHandler(
    (filters.TEXT | filters.VOICE) & (~filters.COMMAND), response_all
)

print("Building app")
application = Application.builder().updater(updater).build()

application.add_handler(response_all_handler)
print("Building is done")


if __name__ == "__main__":
    # run()
    application.run_polling()

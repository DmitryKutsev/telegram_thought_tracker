import json
import os
import datetime

from dotenv import load_dotenv
from openai import OpenAI
from together import Together

from prompts_config import my_prompts

load_dotenv() # TODO: replace with settings

# TODO: put in settings config ASAP
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

TOGETHER_API_KEY = os.getenv("TOGETHER_API_KEY")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

openai_client = OpenAI()


class LlmController:
    def __init__(self, model_name="gpt-4o"):
        self.current_model = model_name

        self.llm_client = (
            Together(api_key=TOGETHER_API_KEY)
            if model_name in TOGETHER_MODELS_LIST
            else openai_client
        )

    def classify_text(self, text):
        curr_prompt = my_prompts.CLASSIFIER_PROMPT.format(USER_INPUT=text)
        response = self.llm_client.chat.completions.create(
            model=self.current_model,
            messages=[
                {
                    "role": "user",
                    "content": curr_prompt,
                }
            ],
        )
        return response.choices[0].message.content
    
    def retreive_custom_info(self, text, username):
        text = text + f" today date: {datetime.datetime.today()}"
        curr_prompt = my_prompts.CUSTOM_RETRIEVER_PROMPT.format(USER_INPUT=text, USER_NAME=username)
        response = self.llm_client.chat.completions.create(
            model=self.current_model,
            messages=[
                {
                    "role": "user",
                    "content": curr_prompt,
                }
            ],
        )
        
        return response.choices[0].message.content
    
    def retreive_thoughts(self, text) -> dict:
        text = text + f" today date: {datetime.datetime.today()}"
        curr_prompt = my_prompts.RETREIVER_PROMPT.format(USER_INPUT=text)
        response = self.llm_client.chat.completions.create(
            model=self.current_model,
            messages=[
                {
                    "role": "user",
                    "content": curr_prompt,
                }
            ],
        )
        my_response = response.choices[0].message.content

        try:
            query_params = json.loads(my_response)
            return query_params
        
        except json.JSONDecodeError:
            raise "Invalid JSON format."

    def transcribe_text(self, temp_path):
        transcription = openai_client.audio.transcriptions.create(
            model="whisper-1", file=open(temp_path, "rb")
        )

        os.remove(temp_path)
        return transcription.text


    def summarize_entries(self, session, params: dict):
        """
        Retrieve and summarize dreams or thoughts for a user within a certain period.

        Args:
            session (Session): SQLAlchemy session.
            params (dict): Dictionary containing the following keys:
                - user_tg_id (int): Telegram user ID to filter entries.
                - entry_type (str): Either "dream", "thought" or "plans".
                - start_date (datetime, optional): Start date for filtering entries. Defaults to None (no filter).
                - end_date (datetime, optional): End date for filtering entries. Defaults to None (no filter).

        Returns:
            str: A summary of the entries.
        """
        user_tg_id = params.get("user_tg_id")
        entry_type = params.get("entry_type")
        start_date = params.get("start_date", datetime.min)
        end_date = params.get("end_date", datetime.utcnow)

        if entry_type not in ["dream", "thought", "plans"]:
            raise ValueError("entry_type must be either 'dream' or 'thought'")

        # Query the database for the relevant entries
        entries = (
            session.query(Thought.text)
            .filter(
                and_(
                    Thought.user_tg_id == user_tg_id,
                    Thought.type == entry_type,
                    Thought.datetime >= start_date,
                    Thought.datetime <= end_date,
                )
            )
            .all()
        )

        # Extract texts from query results
        texts = [entry.text for entry in entries]

        if not texts:
            return f"No {entry_type}s found for the specified period."

        # Prepare the prompt for summarization
        prompt = (
            f"You are an expert text summarizer. Below are multiple {entry_type}s written by a user. "
            f"Please provide a concise and meaningful summary of these {entry_type}s:"
                + "\n\n".join(texts)
            )

        # Example of using a language model for summarization (e.g., OpenAI GPT)
        # Replace `your_gpt_summarization_function` with the actual function you use to call the model
        summary = your_gpt_summarization_function(prompt)

        return summary
    

    def analyze_dreams_or_thoughts(self, content: str) -> str:
        curr_prompt = my_prompts.ANALYZING_PROMPT.format(
            DREAMS_OR_THOUGHTS=content
        )

        response = self.llm_client.chat.completions.create(
            model=self.current_model,
            messages=[
                {
                    "role": "user",
                    "content": curr_prompt,
                }
            ],
        )
        
        return response.choices[0].message.content
    

# Example usage (assuming you have a valid SQLAlchemy session):
# session = Session(bind=engine)
# params = {
#     "user_tg_id": 12345,
#     "entry_type": "dream",
#     "start_date": datetime(2024, 1, 1),
#     "end_date": datetime(2024, 12, 31)
# }
# summary = summarize_entries(session, params)
# print(summary)

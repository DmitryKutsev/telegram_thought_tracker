from openai import OpenAI
from together import Together
import os

from prompts_config import my_prompts


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

    def transcribe_text(self, temp_path):
        transcription = openai_client.audio.transcriptions.create(
            model="whisper-1", file=open(temp_path, "rb")
        )

        os.remove(temp_path)
        return transcription.text

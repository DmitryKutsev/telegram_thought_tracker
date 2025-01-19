from pathlib import Path

import yaml
from pydantic_settings import BaseSettings


class Prompts(BaseSettings):
    CLASSIFIER_PROMPT: str
    RETREIVER_PROMPT: str
    CUSTOM_RETRIEVER_PROMPT: str
    
    @classmethod
    def from_yaml(cls, file_path: str):
        with open(file_path, "r") as file:
            yaml_data = yaml.safe_load(file)
        return cls(**yaml_data)


curr_dir = Path(__file__).parent
yaml_path = curr_dir / "prompts.yaml"

my_prompts = Prompts.from_yaml(str(yaml_path))

# print(my_prompts.CLASSIFIER_PROMPT.format(USER_INPUT="text"))

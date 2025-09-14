
from openai import OpenAI
import openai
import os
from logger_utils import get_logger
client = OpenAI()

logger = get_logger("llm-helper")
def check_api_key():
    api_key = os.environ.get('OPENAI_API_KEY')
    if api_key is None:
        logger.error("Cannot find OpenAI API key in the environment variable. Please set it as $OPENAI_API_KEY")
        exit(1)
        
def language_query(usr_msg, sys_msg, model,seed:int, temperature: float):
    check_api_key()
    try:
        response = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": sys_msg},
                {"role": "user", "content": usr_msg}
            ],
            seed=seed,
            temperature=temperature
        )
        response_content = response.choices[0].message.content
        system_fingerprint = response.system_fingerprint
        prompt_tokens = response.usage.prompt_tokens
        completion_tokens = response.usage.total_tokens - response.usage.prompt_tokens
        model_id = response.model
        model_info = f"""Model ID: {model_id}
Seed: 10
Temperature: 0
System Fingerprint: {system_fingerprint}
Number of prompt tokens: {prompt_tokens}
Number of competetion tokens: {completion_tokens}"""
        logger.info(model_info)
        return response_content, model_info
    except Exception as e:
        logger.error(f"An error occurred: {e}")
        return None

def get_embedding(text, model="text-embedding-3-large"):
    check_api_key()
    response = openai.embeddings.create(model=model, input=text)
    return response.data[0].embedding

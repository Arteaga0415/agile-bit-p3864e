import logging
import json
import asyncio
import os
from openai import OpenAI
client = OpenAI()

logger = logging.getLogger('data-extractor')
logger.setLevel(logging.INFO)

class DataExtractor:
    #por defecto se utilizara el gpt4o-mini pero se puede especificar cualquier otro de openai
    def __init__(self, model='gpt-4o-mini'):
        self.model = model

    """
    Sends the entire conversation transcription to the GPT model and extracts key property details.
    Args:
        conversation_transcription (str): The full transcription of the conversation.
    Returns:
        dict: A dictionary containing the extracted property details.
    """
    def extract_information(self, conversation_transcription: str):
        #Generar prompt para extraer la informacion
        prompt = self._build_prompt(conversation_transcription)
        logger.info('Sending transcription for extraction to LLM')

        # Make the request to OpenAI
        try:
            response = self._send_to_openai(prompt)
            # Parse and return the response
            extracted_info = self._parse_response(response)
            return extracted_info
        except Exception as e:
            logger.error(f"Failed to get a response from OpenAI: {e}")
            return {"error": str(e)}

    """
    Constructs the prompt that will be sent to the GPT model for extraction.
    Args:
        transcription (str): The full transcription of the conversation.
    Returns:
        str: The prompt for the GPT model.
    """
    def _build_prompt(self, transcription: str):
        prompt = (
            "You are a data extraction assistant. I am providing you with a conversation transcription between a real estate assistant and a property owner."
            "Your task is to extract the following information: "
            "House condition (good, outdated, average, or needs work), year built, square footage, number of bedrooms, number of bathrooms, "
            "kitchen condition, flooring condition, electrical and plumbing condition, foundation condition, roof age,"
            "whether HVAC is present, whether a pool is present, whether the property is rented, vacant, or lived in by the owner, "
            "how long it has been in that condition, rental amount, payment frequency, and rental contract expiration date. "
            "Also, include the names of the owner(s) if mentioned. Format the extracted information in a structured JSON format."
            "\n\nConversation Transcription:\n"
            f"{transcription}\n"
            "Please respond only with the structured JSON containing the extracted information."
        )
        return prompt

    """
    Send the prompt to OpenAI and get the response.
    """
    def _send_to_openai(self, prompt: str):
        # Make the API request to OpenAI's Chat Completion API (for GPT-3.5, GPT-4 models)
        response = client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": prompt}
            ]
        )
        logger.info(f"chat response: {response.choices[0].message.content}")
        return response.choices[0].message.content
    
    """
    Parses the response from the GPT model to extract the JSON data.
    Args:
        response_text (str): The response text from the GPT model.
    Returns:
        dict: A dictionary of the extracted information or an error if parsing fails.
    """
    def _parse_response(self, response_text: str):
        try:
            cleaned_response = response_text.strip("```json").strip("```").strip()
            extracted_info = json.loads(cleaned_response)
            return extracted_info
        except json.JSONDecodeError as error: 
            logger.error(f"Failed to parse GPT Response: {error}")
            return {"error": "Failed to parse GPT Response"}

async def run_extraction(conversation_transcription: str):
    extractor = DataExtractor()
    extracted_data = await extractor.extract_information(conversation_transcription)
    return extracted_data

if __name__ == "__main__":
    extracted_data = asyncio.run(run_extraction(transcription))
    print(extracted_data)
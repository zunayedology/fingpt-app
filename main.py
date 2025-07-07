from fastapi import FastAPI, Request
from pydantic import BaseModel
from transformers import AutoModelForCausalLM, AutoTokenizer
from peft import PeftModel
from dotenv import load_dotenv
import os
import requests
import re
import logging
import bleach
import torch

# Set up logging to file and console
logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("main.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()
hf_token = os.getenv("HF_TOKEN")
if not hf_token:
    logger.error("HF_TOKEN not found in .env file")
    raise EnvironmentError("HF_TOKEN not found in .env file. Please set your Hugging Face access token.")

app = FastAPI()

# Initialize FinGPT on CPU
base_model_name = "meta-llama/Llama-2-7b-chat-hf"
lora_model_name = "FinGPT/fingpt-forecaster_dow30_llama2-7b_lora"
try:
    logger.info(f"Loading base model: {base_model_name}")
    base_model = AutoModelForCausalLM.from_pretrained(
        base_model_name,
        token=hf_token,
        device_map="cpu",
        torch_dtype=torch.float16,  # Use float16 to reduce memory
        low_cpu_mem_usage=True  # Optimize memory usage
    )
    logger.info(f"Loading LoRA adapter: {lora_model_name}")
    model = PeftModel.from_pretrained(base_model, lora_model_name, token=hf_token)
    logger.info(f"Loading tokenizer for: {base_model_name}")
    tokenizer = AutoTokenizer.from_pretrained(base_model_name, token=hf_token)
except Exception as e:
    logger.error(f"Failed to load model {base_model_name} or LoRA {lora_model_name}: {str(e)}")
    raise

class Query(BaseModel):
    text: str

def extract_account_id(query):
    match = re.search(r"\b\d{6}\b", query)
    return match.group(0) if match else "123456"  # Default for testing

def extract_loan_type(query):
    for loan in ["home_loan", "personal_loan"]:
        if loan in query.lower():
            return loan
    return "home_loan"  # Default for testing

def extract_appointment_details(query):
    date = "2025-07-10"  # Static for demo
    time = "10:00 AM"    # Static for demo
    return date, time

@app.post("/query")
async def handle_query(query: Query):
    # Sanitize user input
    clean_text = bleach.clean(query.text)
    logger.debug(f"Processing query: {clean_text}")
    text = clean_text.lower()
    
    # Handle specific front-desk tasks
    if "account balance" in text or "account details" in text:
        account_id = extract_account_id(text)
        try:
            response = requests.post("http://localhost:8000/tools/account_balance", json={"account_id": account_id})
            response.raise_for_status()
            return {"response": response.json()["result"]}
        except requests.RequestException as e:
            logger.error(f"Account balance request failed: {str(e)}")
            return {"response": f"Error: {str(e)}"}
    
    elif "loan" in text or "interest rate" in text:
        loan_type = extract_loan_type(text)
        try:
            response = requests.post("http://localhost:8000/tools/loan_details", json={"loan_type": loan_type})
            response.raise_for_status()
            return {"response": response.json()["result"]}
        except requests.RequestException as e:
            logger.error(f"Loan details request failed: {str(e)}")
            return {"response": f"Error: {str(e)}"}
    
    elif "appointment" in text or "schedule" in text:
        account_id = extract_account_id(text)
        date, time = extract_appointment_details(text)
        try:
            response = requests.post("http://localhost:8000/tools/schedule_appointment", json={"account_id": account_id, "date": date, "time": time})
            response.raise_for_status()
            return {"response": response.json()["result"]}
        except requests.RequestException as e:
            logger.error(f"Appointment request failed: {str(e)}")
            return {"response": f"Error: {str(e)}"}
    
    else:
        # Use FinGPT for general financial queries or stock forecasting
        try:
            logger.debug("Tokenizing input")
            inputs = tokenizer(clean_text, return_tensors="pt", max_length=512, truncation=True).to("cpu")
            logger.debug("Generating response")
            outputs = model.generate(**inputs, max_length=100)  # Reduced for faster inference
            response = tokenizer.decode(outputs[0], skip_special_tokens=True)
            logger.debug(f"Generated response: {response}")
            return {"response": response}
        except Exception as e:
            logger.error(f"FinGPT generation failed: {str(e)}")
            return {"response": "Error: Could not generate response."}

if __name__ == "__main__":
    import uvicorn
    logger.info("Starting FastAPI server")
    uvicorn.run(app, host="0.0.0.0", port=5000)
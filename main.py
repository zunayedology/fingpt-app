from fastapi import FastAPI, Request
from pydantic import BaseModel
from transformers import AutoModelForCausalLM, AutoTokenizer
from peft import PeftModel
from dotenv import load_dotenv
import os
import requests
import re
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()
hf_token = os.getenv("HF_TOKEN")
if not hf_token:
    raise EnvironmentError("HF_TOKEN not found in .env file. Please set your Hugging Face access token.")

app = FastAPI()

# Initialize FinGPT with LoRA
base_model_name = "meta-llama/Llama-2-7b-chat-hf"
lora_model_name = "FinGPT/fingpt-forecaster_dow30_llama2-7b_lora"
try:
    # Load base model
    base_model = AutoModelForCausalLM.from_pretrained(
        base_model_name,
        token=hf_token,
        device_map="auto",
        load_in_4bit=True  # 4-bit quantization for memory efficiency
    )
    # Load LoRA adapter
    model = PeftModel.from_pretrained(base_model, lora_model_name, token=hf_token)
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
    logger.info(f"Processing query: {query.text}")
    text = query.text.lower()
    
    # Handle specific front-desk tasks
    if "account balance" in text or "account details" in text:
        account_id = extract_account_id(text)
        response = requests.post("http://localhost:8000/tools/account_balance", json={"account_id": account_id})
        if response.status_code == 200:
            return {"response": response.json()["result"]}
        return {"response": f"Error: {response.json()['detail']}"}
    
    elif "loan" in text or "interest rate" in text:
        loan_type = extract_loan_type(text)
        response = requests.post("http://localhost:8000/tools/loan_details", json={"loan_type": loan_type})
        if response.status_code == 200:
            return {"response": response.json()["result"]}
        return {"response": f"Error: {response.json()['detail']}"}
    
    elif "appointment" in text or "schedule" in text:
        account_id = extract_account_id(text)
        date, time = extract_appointment_details(text)
        response = requests.post("http://localhost:8000/tools/schedule_appointment", json={"account_id": account_id, "date": date, "time": time})
        if response.status_code == 200:
            return {"response": response.json()["result"]}
        return {"response": f"Error: {response.json()['detail']}"}
    
    else:
        # Use FinGPT for general financial queries or stock forecasting
        try:
            inputs = tokenizer(query.text, return_tensors="pt", max_length=512, truncation=True)
            outputs = model.generate(**inputs, max_length=200)
            response = tokenizer.decode(outputs[0], skip_special_tokens=True)
            return {"response": response}
        except Exception as e:
            logger.error(f"FinGPT generation failed: {str(e)}")
            return {"response": "Error: Could not generate response."}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=5000)
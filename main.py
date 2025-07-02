from fastapi import FastAPI, Request
from pydantic import BaseModel
from transformers import AutoModelForCausalLM, AutoTokenizer
from modelcontextprotocol import MCPClient
import re

app = FastAPI()

# Initialize FinGPT
model_name = "FinGPT/fingpt-llama2-7b"
tokenizer = AutoTokenizer.from_pretrained(model_name)
model = AutoModelForCausalLM.from_pretrained(model_name, device_map="auto")

# Initialize MCP Client
mcp_client = MCPClient(server_url="http://localhost:8000")

class Query(BaseModel):
    text: str

def extract_account_id(query):
    # Simple regex to extract account ID (e.g., "123456")
    match = re.search(r"\b\d{6}\b", query)
    return match.group(0) if match else "123456"  # Default for testing

def extract_loan_type(query):
    # Simple keyword matching for loan type
    for loan in ["home_loan", "personal_loan"]:
        if loan in query.lower():
            return loan
    return "home_loan"  # Default for testing

def extract_appointment_details(query):
    # Dummy extraction; improve with NLP for production
    date = "2025-07-10"  # Static for demo
    time = "10:00 AM"    # Static for demo
    return date, time

@app.post("/query")
async def handle_query(query: Query):
    text = query.text.lower()
    
    # Handle specific front-desk tasks
    if "account balance" in text or "account details" in text:
        account_id = extract_account_id(text)
        result = mcp_client.execute_tool("account_balance", {"account_id": account_id})
        return {"response": result}
    
    elif "loan" in text or "interest rate" in text:
        loan_type = extract_loan_type(text)
        result = mcp_client.execute_tool("loan_details", {"loan_type": loan_type})
        return {"response": result}
    
    elif "appointment" in text or "schedule" in text:
        account_id = extract_account_id(text)
        date, time = extract_appointment_details(text)
        result = mcp_client.execute_tool("schedule_appointment", {"account_id": account_id, "date": date, "time": time})
        return {"response": result}
    
    else:
        # Use FinGPT for general financial queries
        inputs = tokenizer(query.text, return_tensors="pt", max_length=512, truncation=True)
        outputs = model.generate(**inputs, max_length=200)
        response = tokenizer.decode(outputs[0], skip_special_tokens=True)
        return {"response": response}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=5000)
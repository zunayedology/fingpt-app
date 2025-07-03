from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import requests

app = FastAPI(title="IDLC MCP-Like Tool Server")

class AccountBalanceRequest(BaseModel):
    account_id: str

class LoanDetailsRequest(BaseModel):
    loan_type: str

class AppointmentRequest(BaseModel):
    account_id: str
    date: str
    time: str

@app.post("/tools/account_balance")
async def account_balance(request: AccountBalanceRequest):
    response = requests.get(f"http://localhost:8001/account/{request.account_id}")
    data = response.json()
    if data["status"] == "success":
        return {"result": f"Account {request.account_id} balance: ${data['data']['balance']} (Account Holder: {data['data']['name']})"}
    raise HTTPException(status_code=404, detail="Account not found")

@app.post("/tools/loan_details")
async def loan_details(request: LoanDetailsRequest):
    response = requests.get(f"http://localhost:8001/loan/{request.loan_type}")
    data = response.json()
    if data["status"] == "success":
        return {"result": f"{request.loan_type} details: Interest Rate: {data['data']['interest_rate']}%, Max Amount: ${data['data']['max_amount']}, Tenure: {data['data']['tenure_years']} years"}
    raise HTTPException(status_code=404, detail="Loan type not found")

@app.post("/tools/schedule_appointment")
async def schedule_appointment(request: AppointmentRequest):
    response = requests.post("http://localhost:8001/appointment", json={"account_id": request.account_id, "date": request.date, "time": request.time})
    data = response.json()
    if data["status"] == "success":
        return {"result": f"Appointment scheduled for {request.account_id} on {request.date} at {request.time}. Confirmation: {data['data']['confirmation']}"}
    raise HTTPException(status_code=400, detail="Could not schedule appointment")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
from fastapi import FastAPI
from pydantic import BaseModel
from datetime import datetime
import uvicorn

app = FastAPI()

# Dummy data
ACCOUNTS = {
    "123456": {"balance": 5000.00, "name": "John Doe", "account_type": "Savings"},
    "789012": {"balance": 15000.00, "name": "Jane Smith", "account_type": "Current"}
}

LOANS = {
    "home_loan": {"interest_rate": 5.5, "max_amount": 1000000, "tenure_years": 20},
    "personal_loan": {"interest_rate": 8.0, "max_amount": 50000, "tenure_years": 5}
}

APPOINTMENTS = []

class AccountRequest(BaseModel):
    account_id: str

class LoanRequest(BaseModel):
    loan_type: str

class AppointmentRequest(BaseModel):
    account_id: str
    date: str
    time: str

@app.get("/account/{account_id}")
async def get_account_balance(account_id: str):
    if account_id in ACCOUNTS:
        return {"status": "success", "data": ACCOUNTS[account_id]}
    return {"status": "error", "message": "Account not found"}

@app.get("/loan/{loan_type}")
async def get_loan_details(loan_type: str):
    if loan_type in LOANS:
        return {"status": "success", "data": LOANS[loan_type]}
    return {"status": "error", "message": "Loan type not found"}

@app.post("/appointment")
async def schedule_appointment(appointment: AppointmentRequest):
    appointment_data = {
        "account_id": appointment.account_id,
        "date": appointment.date,
        "time": appointment.time,
        "confirmation": f"APPT-{len(APPOINTMENTS) + 1}"
    }
    APPOINTMENTS.append(appointment_data)
    return {"status": "success", "data": appointment_data}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8001)
    
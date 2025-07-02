from modelcontextprotocol import MCPServer, Tool
import requests
import json

class AccountBalanceTool(Tool):
    def __init__(self):
        super().__init__(name="account_balance", description="Fetches account balance for a given account ID")
    
    def execute(self, params):
        account_id = params.get("account_id")
        response = requests.get(f"http://localhost:8001/account/{account_id}")
        data = response.json()
        if data["status"] == "success":
            return f"Account {account_id} balance: ${data['data']['balance']} (Account Holder: {data['data']['name']})"
        return "Error: Account not found"

class LoanDetailsTool(Tool):
    def __init__(self):
        super().__init__(name="loan_details", description="Fetches details for a specific loan type")
    
    def execute(self, params):
        loan_type = params.get("loan_type")
        response = requests.get(f"http://localhost:8001/loan/{loan_type}")
        data = response.json()
        if data["status"] == "success":
            return f"{loan_type} details: Interest Rate: {data['data']['interest_rate']}%, Max Amount: ${data['data']['max_amount']}, Tenure: {data['data']['tenure_years']} years"
        return "Error: Loan type not found"

class AppointmentTool(Tool):
    def __init__(self):
        super().__init__(name="schedule_appointment", description="Schedules an appointment for a customer")
    
    def execute(self, params):
        account_id = params.get("account_id")
        date = params.get("date")
        time = params.get("time")
        response = requests.post("http://localhost:8001/appointment", json={"account_id": account_id, "date": date, "time": time})
        data = response.json()
        if data["status"] == "success":
            return f"Appointment scheduled for {account_id} on {date} at {time}. Confirmation: {data['data']['confirmation']}"
        return "Error: Could not schedule appointment"

if __name__ == "__main__":
    server = MCPServer(tools=[AccountBalanceTool(), LoanDetailsTool(), AppointmentTool()])
    server.run(port=8000)
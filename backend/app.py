from flask import Flask, request, jsonify
from backend.agent import ScheduleOptimizationAgent
import os
from dotenv import load_dotenv
import json

load_dotenv()

app = Flask(__name__)

# Example treatment plans for testing
example_treatment_plans = [
    {"name": "Basic Checkup", "cost": 100},
    {"name": "Dental Cleaning", "cost": 150},
    {"name": "Cavity Filling", "cost": 200},
    {"name": "Root Canal", "cost": 800},
    {"name": "Tooth Extraction", "cost": 250},
    {"name": "Dental Crown", "cost": 1000},
    {"name": "Teeth Whitening", "cost": 300},
    {"name": "Dental Implant", "cost": 3000},
    {"name": "Orthodontic Consultation", "cost": 150},
    {"name": "Wisdom Tooth Removal", "cost": 450}
]

@app.route('/optimize_schedule', methods=['POST'])
def api_optimize_schedule():
    data = request.json
    treatment_plans = data['treatment_plans']
    revenue_target = data['revenue_target']
    num_slots = data['num_slots']
    
    api_key = os.getenv('ANTHROPIC_API_KEY')
    
    agent = ScheduleOptimizationAgent(api_key=api_key)
    result = agent.optimize_schedule(treatment_plans, revenue_target, num_slots)
    return jsonify(result)

def test_optimize_schedule_locally():
    revenue_target = 5000
    num_slots = 8

    api_key = os.getenv('ANTHROPIC_API_KEY')
    
    agent = ScheduleOptimizationAgent(api_key=api_key)
    result = agent.optimize_schedule(example_treatment_plans, revenue_target, num_slots)
    print("Optimization Result:")
    print(json.dumps(result, indent=2))

if __name__ == '__main__':
    test_optimize_schedule_locally()
    
    # Comment out the line below if you want to run the local test instead of starting the Flask server
    # app.run(debug=True)
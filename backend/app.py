from flask import Flask, request, jsonify
from agent import ScheduleOptimizationAgent
import os
from dotenv import load_dotenv
import json
from datetime import datetime, timedelta

load_dotenv()

app = Flask(__name__)

# Example treatment plans for testing
example_treatment_plans = [
    {"id": 1, "name": "Basic Checkup", "cost": 100},
    {"id": 1, "name": "Dental Cleaning", "cost": 150},
    {"id": 1, "name": "Cavity Filling", "cost": 200},
    {"id": 2, "name": "Root Canal", "cost": 800},
    {"id": 2, "name": "Tooth Extraction", "cost": 250},
    {"id": 2, "name": "Dental Crown", "cost": 1000},
    {"id": 3, "name": "Teeth Whitening", "cost": 300},
    {"id": 3, "name": "Dental Implant", "cost": 3000},
    {"id": 4, "name": "Orthodontic Consultation", "cost": 150},
    {"id": 4, "name": "Wisdom Tooth Removal", "cost": 450}
]

# Generate example partial schedule for the next 5 weekdays
def generate_example_partial_schedule():
    partial_schedule = []
    current_date = datetime.now().date()
    weekdays_added = 0
    while weekdays_added < 5:
        if current_date.weekday() < 5: 
            partial_schedule.append({
                "date": current_date.strftime("%Y-%m-%d"),
                "treatment": "Basic Checkup",
                "patient_id": weekdays_added + 1,
                "cost": 100
            })
            weekdays_added += 1
        current_date += timedelta(days=1)
    return partial_schedule

@app.route('/optimize_schedule', methods=['POST'])
def api_optimize_schedule():
    data = request.json
    partial_schedule = data['partial_schedule']
    treatment_plans = data['treatment_plans']
    revenue_target = data['revenue_target']
    
    api_key = os.getenv('ANTHROPIC_API_KEY')
    
    agent = ScheduleOptimizationAgent(api_key=api_key)
    result = agent.optimize_schedule(partial_schedule, treatment_plans, revenue_target)
    return jsonify(result)

def test_optimize_schedule_locally():
    revenue_target = 10000
    example_partial_schedule = generate_example_partial_schedule()

    api_key = os.getenv('ANTHROPIC_API_KEY')
    
    agent = ScheduleOptimizationAgent(api_key=api_key)
    result = agent.optimize_schedule(example_partial_schedule, example_treatment_plans, revenue_target)
    print("Optimization Result:")
    print(json.dumps(result, indent=2))

    # Output the result to a JSON file
    output_file = 'optimized_schedule.json'
    with open(output_file, 'w') as f:
        json.dump(result, f, indent=2)
    print(f"Optimized schedule has been saved to {output_file}")

if __name__ == '__main__':
    test_optimize_schedule_locally()
    
    # Comment out the line below if you want to run the local test instead of starting the Flask server
    # app.run(debug=True)
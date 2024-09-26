from flask import Flask, request, jsonify
from agent import ScheduleOptimizationAgent
import os
from dotenv import load_dotenv
import json
from example_input import EXAMPLE_TREATMENT_PLANS, NUM_SLOTS

load_dotenv()

app = Flask(__name__)

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
    revenue_target = 500000  # Increased revenue target for the larger scale
    num_slots = NUM_SLOTS  # Use the fixed number of slots (720)

    api_key = os.getenv('ANTHROPIC_API_KEY')
    
    agent = ScheduleOptimizationAgent(api_key=api_key)
    result = agent.optimize_schedule(EXAMPLE_TREATMENT_PLANS, revenue_target, num_slots)
    
    if "error" in result:
        print(f"Error: {result['error']}")
    else:
        print("Optimization Result:")
        print(f"Total appointments scheduled: {len(result['schedule'])}")
        print(f"Total revenue: ${result['total_revenue']:.2f}")
        print(f"Revenue target met: {result['revenue_target_met']}")
        print(f"Analysis: {result['analysis']}")

        # Output the result to a JSON file
        output_file = 'optimized_schedule.json'
        with open(output_file, 'w') as f:
            json.dump(result, f, indent=2)
        print(f"Optimized schedule has been saved to {output_file}")

if __name__ == '__main__':
    test_optimize_schedule_locally()
    
    # Comment out the line below if you want to run the local test instead of starting the Flask server
    # app.run(debug=True)
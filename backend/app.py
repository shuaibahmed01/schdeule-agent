from flask import Flask, request, jsonify
from backend.agent import ScheduleOptimizationAgent
import os
from dotenv import load_dotenv


load_dotenv()

app = Flask(__name__)

@app.route('/optimize_schedule', methods=['POST'])
def api_optimize_schedule():
    data = request.json
    treatment_plans = data['treatment_plans']
    revenue_target = data['revenue_target']
    num_slots = data['num_slots']

    
    api_key = os.getenv('OPENAI_API_KEY')
    
    agent = ScheduleOptimizationAgent(api_key=api_key)
    result = agent.optimize_schedule(treatment_plans, revenue_target, num_slots)
    return jsonify(result)

if __name__ == '__main__':
    app.run(debug=True)
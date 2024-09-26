import random
from datetime import datetime, timedelta
import calendar

def generate_example_input(num_appointments=720):
    treatments = [
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

    example_treatment_plans = []
    for i in range(num_appointments):
        patient_id = random.randint(1, 100)  # Assuming 100 different patients
        treatment = random.choice(treatments)
        example_treatment_plans.append({
            "id": patient_id,
            "name": treatment["name"],
            "cost": treatment["cost"]
        })

    return example_treatment_plans

def get_next_month_weekdays():
    today = datetime.now()
    next_month = today.replace(day=1) + timedelta(days=32)
    first_day = next_month.replace(day=1)
    _, last_day = calendar.monthrange(first_day.year, first_day.month)
    last_date = first_day.replace(day=last_day)

    weekdays = []
    current_day = first_day
    while current_day <= last_date:
        if current_day.weekday() < 5:  # Monday = 0, Friday = 4
            weekdays.append(current_day.strftime("%Y-%m-%d"))
        current_day += timedelta(days=1)
    
    return weekdays

EXAMPLE_TREATMENT_PLANS = generate_example_input(720)
NEXT_MONTH_WEEKDAYS = get_next_month_weekdays()
NUM_SLOTS = 720  # Fixed number of slots
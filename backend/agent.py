from langchain_anthropic import ChatAnthropic
from langchain_core.prompts import ChatPromptTemplate
from langchain.output_parsers import PydanticOutputParser
from pydantic import BaseModel, Field
from typing import List, Dict
import json
from datetime import datetime, timedelta
from example_input import NEXT_MONTH_WEEKDAYS

class ScheduledTreatment(BaseModel):
    date: str = Field(description="Date of the treatment in YYYY-MM-DD format")
    treatment: str = Field(description="Name of the treatment")
    patient_id: int = Field(description="ID of the patient")
    cost: float = Field(description="Cost of the treatment")

class ScheduleOutput(BaseModel):
    schedule: List[ScheduledTreatment] = Field(description="List of scheduled treatments")
    total_revenue: float = Field(description="Total revenue for the schedule")
    revenue_target_met: bool = Field(description="Boolean indicating if the revenue target was met")
    analysis: str = Field(description="Brief explanation of the scheduling strategy")

class ScheduleOptimizationAgent:
    def __init__(self, api_key: str, max_retries: int = 3):
        self.llm = ChatAnthropic(model="claude-3-sonnet-20240229", anthropic_api_key=api_key)
        self.output_parser = PydanticOutputParser(pydantic_object=ScheduleOutput)
        self.max_retries = max_retries

    def optimize_schedule(self, partial_schedule: List[Dict], treatment_plans: List[Dict], revenue_target: float) -> Dict:
        """Optimize the doctor's schedule using Claude-3.5-sonnet with retry mechanism."""
        available_slots = self._get_available_slots(partial_schedule)
        prompt = self._create_prompt(partial_schedule, treatment_plans, revenue_target, available_slots)
        
        for attempt in range(self.max_retries):
            try:
                response = self._get_claude_response(prompt)
                return self._parse_response(response)
            except Exception as e:
                if attempt == self.max_retries - 1:
                    return {"error": f"Failed to parse the AI response after {self.max_retries} attempts: {str(e)}"}
                print(f"Attempt {attempt + 1} failed. Retrying...")

    def _get_available_slots(self, partial_schedule: List[Dict]) -> Dict[str, int]:
        """Calculate available slots for each weekday in the next month."""
        today = datetime.now().date()
        end_date = today + timedelta(days=30)
        date_range = [today + timedelta(days=x) for x in range((end_date - today).days + 1) if (today + timedelta(days=x)).weekday() < 5]
        
        available_slots = {date.strftime("%Y-%m-%d"): 3 for date in date_range}
        
        for appointment in partial_schedule:
            date = appointment['date']
            if date in available_slots:
                available_slots[date] -= 1
        
        return {date: slots for date, slots in available_slots.items() if slots > 0}

    def _create_prompt(self, partial_schedule: List[Dict], treatment_plans: List[Dict], revenue_target: float, available_slots: Dict[str, int]) -> str:
        """Create a detailed prompt for the Claude model."""
        formatted_plans = self._format_treatment_plans(treatment_plans)
        formatted_partial_schedule = self._format_partial_schedule(partial_schedule)
        formatted_available_slots = self._format_available_slots(available_slots)
        
        template = """As an AI scheduling assistant specializing in healthcare optimization, your task is to complete a partial schedule for a doctor based on the following parameters:

        Partial Schedule:
        {formatted_partial_schedule}

        Available Slots:
        {formatted_available_slots}

        Treatment Plans:
        {formatted_plans}

        Revenue Target: ${revenue_target}

        Objective:
        Complete the schedule by filling in the available slots to maximize revenue while meeting or exceeding the revenue target. Consider the following factors:
        1. Prioritize higher-revenue treatments when possible.
        2. Ensure a balanced mix of treatments to avoid overbooking any single type.
        3. If the revenue target can't be met, get as close as possible.
        4. Spread out treatments for each patient (identified by patient_id) so they don't have multiple appointments on the same day.
        5. Respect the maximum of 3 appointments per day.
        6. Only schedule appointments on weekdays (Monday to Friday).
        7. Use only the dates provided in the Available Slots section.

        Instructions:
        1. Analyze the partial schedule, available slots, and treatment plans.
        2. Fill in the available slots with treatments from the treatment plans.
        3. Ensure that no patient has more than one appointment per day.
        4. Calculate the total revenue for the complete schedule.
        5. Determine if the revenue target is met.

        {format_instructions}

        Remember, you are an AI assistant focused on optimizing healthcare schedules. Provide your best solution based on the given constraints and objectives.
        """
        
        prompt = ChatPromptTemplate.from_template(template)
        
        return prompt.format(
            formatted_partial_schedule=formatted_partial_schedule,
            formatted_available_slots=formatted_available_slots,
            formatted_plans=formatted_plans,
            revenue_target=revenue_target,
            format_instructions=self.output_parser.get_format_instructions()
        )

    def _get_claude_response(self, prompt: str) -> str:
        """Get a response from the Claude model."""
        response = self.llm.predict(prompt)
        return response

    def _parse_response(self, response: str) -> Dict:
        """Parse the Claude response into a structured format."""
        try:
            parsed_output = self.output_parser.parse(response)
            return parsed_output.dict()
        except Exception as e:
            raise Exception(f"Failed to parse the AI response: {str(e)}")

    def _format_treatment_plans(self, treatment_plans: List[Dict]) -> str:
        """Format treatment plans for the prompt."""
        return "\n".join([f"- Patient ID: {plan['id']}, Treatment: {plan['name']}, Cost: ${plan['cost']}" for plan in treatment_plans])

    def _format_partial_schedule(self, partial_schedule: List[Dict]) -> str:
        """Format partial schedule for the prompt."""
        return "\n".join([f"- Date: {appt['date']}, Treatment: {appt['treatment']}, Patient ID: {appt['patient_id']}, Cost: ${appt['cost']}" for appt in partial_schedule])

    def _format_available_slots(self, available_slots: Dict[str, int]) -> str:
        """Format available slots for the prompt."""
        return "\n".join([f"- Date: {date}, Available Slots: {slots}" for date, slots in available_slots.items()])

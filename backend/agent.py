from langchain_anthropic import ChatAnthropic
from langchain_core.prompts import ChatPromptTemplate
from langchain.output_parsers import PydanticOutputParser
from pydantic import BaseModel, Field
from typing import List, Dict
import json
from datetime import datetime
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
    def __init__(self, api_key: str):
        self.llm = ChatAnthropic(model="claude-3-sonnet-20240229", anthropic_api_key=api_key)
        self.output_parser = PydanticOutputParser(pydantic_object=ScheduleOutput)

    def optimize_schedule(self, treatment_plans: List[Dict], revenue_target: float, num_slots: int) -> Dict:
        """Optimize the doctor's schedule using Claude-3.5-sonnet."""
        chunk_size = 50  # Process 50 appointments at a time
        schedule = []
        total_revenue = 0
        available_dates = NEXT_MONTH_WEEKDAYS.copy()

        for i in range(0, len(treatment_plans), chunk_size):
            chunk = treatment_plans[i:i+chunk_size]
            chunk_slots = min(num_slots - len(schedule), chunk_size)
            
            if chunk_slots <= 0:
                break

            prompt = self._create_prompt(chunk, revenue_target - total_revenue, chunk_slots, available_dates)
            response = self._get_claude_response(prompt)
            chunk_result = self._parse_response(response)

            if "error" in chunk_result:
                print(f"Error in chunk {i//chunk_size + 1}: {chunk_result['error']}")
                continue

            valid_treatments = [t for t in chunk_result['schedule'] if self._is_valid_treatment(t)]
            schedule.extend(valid_treatments)
            total_revenue += sum(t.cost for t in valid_treatments)

            # Update available dates
            used_dates = set(t.date for t in valid_treatments)
            available_dates = [date for date in available_dates if date not in used_dates]

        revenue_target_met = total_revenue >= revenue_target
        analysis = f"Scheduled {len(schedule)} appointments. Total revenue: ${total_revenue:.2f}. Target {'met' if revenue_target_met else 'not met'}."

        return {
            "schedule": [treatment.dict() for treatment in schedule],
            "total_revenue": total_revenue,
            "revenue_target_met": revenue_target_met,
            "analysis": analysis
        }

    def _is_valid_treatment(self, treatment: ScheduledTreatment) -> bool:
        """Check if a treatment has all required fields."""
        return all([treatment.date, treatment.treatment, treatment.patient_id, treatment.cost])

    def _create_prompt(self, treatment_plans: List[Dict], revenue_target: float, num_slots: int, available_dates: List[str]) -> str:
        """Create a detailed prompt for the Claude model."""
        formatted_plans = self._format_treatment_plans(treatment_plans)
        formatted_dates = ", ".join(available_dates)
        template = """
        As an AI scheduling assistant specializing in healthcare optimization, your task is to create an optimal schedule for a doctor based on the following parameters:

        Treatment Plans:
        {formatted_plans}

        Revenue Target: ${revenue_target}
        Number of Available Slots: {num_slots}
        Available Dates: {formatted_dates}

        Objective:
        Create a schedule that maximizes revenue while meeting or exceeding the revenue target. Consider the following factors:
        1. Prioritize higher-revenue treatments when possible.
        2. Ensure a balanced mix of treatments to avoid overbooking any single type.
        3. If the revenue target can't be met, get as close as possible.
        4. Spread out treatments for each patient (identified by patient_id) so they don't have multiple appointments on the same day.
        5. Assign each treatment to a specific date from the available dates provided.

        Instructions:
        1. Analyze the treatment plans and their costs.
        2. Create a schedule filling all available slots with treatments, assigning specific dates to each treatment.
        3. Ensure that no patient has more than one appointment per day.
        4. Calculate the total revenue for the schedule.
        5. Determine if the revenue target is met.

        {format_instructions}

        Ensure that the "schedule" list contains exactly {num_slots} treatments, each with a unique date from the available dates.

        Remember, you are an AI assistant focused on optimizing healthcare schedules. Provide your best solution based on the given constraints and objectives.
        """
        
        prompt = ChatPromptTemplate.from_template(template)
        
        return prompt.format(
            formatted_plans=formatted_plans,
            revenue_target=revenue_target,
            num_slots=num_slots,
            formatted_dates=formatted_dates,
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
            return {"error": f"Failed to parse the AI response: {str(e)}"}

    def _format_treatment_plans(self, treatment_plans: List[Dict]) -> str:
        """Format treatment plans for the prompt."""
        return "\n".join([f"- Patient ID: {plan['id']}, Treatment: {plan['name']}, Cost: ${plan['cost']}" for plan in treatment_plans])

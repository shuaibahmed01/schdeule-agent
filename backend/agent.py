from langchain_anthropic import ChatAnthropic
from langchain_core.prompts import ChatPromptTemplate
from langchain.output_parsers import PydanticOutputParser
from pydantic import BaseModel, Field
from typing import List, Dict
import json
from datetime import datetime, timedelta

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
        prompt = self._create_prompt(treatment_plans, revenue_target, num_slots)
        response = self._get_claude_response(prompt)
        return self._parse_response(response)

    def _create_prompt(self, treatment_plans: List[Dict], revenue_target: float, num_slots: int) -> str:
        """Create a detailed prompt for the Claude model."""
        formatted_plans = self._format_treatment_plans(treatment_plans)
        start_date = datetime.now().strftime("%Y-%m-%d")
        template = """As an AI scheduling assistant specializing in healthcare optimization, your task is to create an optimal schedule for a doctor based on the following parameters:

        Treatment Plans:
        {formatted_plans}

        Revenue Target: ${revenue_target}
        Number of Available Slots: {num_slots}
        Start Date: {start_date}

        Objective:
        Create a schedule that maximizes revenue while meeting or exceeding the revenue target. Consider the following factors:
        1. Prioritize higher-revenue treatments when possible.
        2. Ensure a balanced mix of treatments to avoid overbooking any single type.
        3. If the revenue target can't be met, get as close as possible.
        4. Spread out treatments for each patient (identified by patient_id) so they don't have multiple appointments on the same day.
        5. Assign each treatment to a specific date, starting from the given start date and using weekdays only.

        Instructions:
        1. Analyze the treatment plans and their costs.
        2. Create a schedule filling all available slots with treatments, assigning specific dates to each treatment.
        3. Ensure that no patient has more than one appointment per day.
        4. Calculate the total revenue for the schedule.
        5. Determine if the revenue target is met.

        {format_instructions}

        Ensure that the "schedule" list contains exactly {num_slots} treatments, each with a unique date (weekdays only).

        Remember, you are an AI assistant focused on optimizing healthcare schedules. Provide your best solution based on the given constraints and objectives.
        """
        
        prompt = ChatPromptTemplate.from_template(template)
        
        return prompt.format(
            formatted_plans=formatted_plans,
            revenue_target=revenue_target,
            num_slots=num_slots,
            start_date=start_date,
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

from langchain_anthropic import ChatAnthropic
from langchain_core.prompts import ChatPromptTemplate
from langchain.output_parsers import PydanticOutputParser
from pydantic import BaseModel, Field
from typing import List, Dict
import json

class ScheduleOutput(BaseModel):
    schedule: List[str] = Field(description="List of treatment names in the optimized schedule")
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
        template = """As an AI scheduling assistant specializing in healthcare optimization, your task is to create an optimal schedule for a doctor based on the following parameters:

        Treatment Plans:
        {formatted_plans}

        Revenue Target: ${revenue_target}
        Number of Available Slots: {num_slots}

        Objective:
        Create a schedule that maximizes revenue while meeting or exceeding the revenue target. Consider the following factors:
        1. Prioritize higher-revenue treatments when possible.
        2. Ensure a balanced mix of treatments to avoid overbooking any single type.
        3. If the revenue target can't be met, get as close as possible.

        Instructions:
        1. Analyze the treatment plans and their costs.
        2. Create a schedule filling all available slots with treatments.
        3. Calculate the total revenue for the schedule.
        4. Determine if the revenue target is met.

        {format_instructions}

        Ensure that the "schedule" list contains exactly {num_slots} treatments.

        Remember, you are an AI assistant focused on optimizing healthcare schedules. Provide your best solution based on the given constraints and objectives.
        """
        
        prompt = ChatPromptTemplate.from_template(template)
        
        return prompt.format(
            formatted_plans=formatted_plans,
            revenue_target=revenue_target,
            num_slots=num_slots,
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
        plan = "\n".join([f"- {plan['name']}: ${plan['cost']}" for plan in treatment_plans])
        print(plan)
        return plan

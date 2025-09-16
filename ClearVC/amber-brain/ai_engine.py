"""
AI Engine for Amber Brain
Handles all AI/LLM interactions and intelligence generation
"""

import json
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime
import os
from dotenv import load_dotenv

import openai
from langchain_openai import ChatOpenAI
from langchain.schema import HumanMessage, SystemMessage, AIMessage
from langchain.memory import ConversationSummaryBufferMemory
import httpx

load_dotenv()

logger = logging.getLogger(__name__)

class AIEngine:
    """
    Core AI engine for intelligent processing
    """

    def __init__(self):
        self.openai_api_key = os.getenv('OPENAI_API_KEY')
        self.cloudflare_account_id = os.getenv('CLOUDFLARE_ACCOUNT_ID')
        self.cloudflare_api_token = os.getenv('CLOUDFLARE_API_TOKEN')

        # Initialize OpenAI
        openai.api_key = self.openai_api_key

        # Initialize LangChain LLM
        self.llm = ChatOpenAI(
            temperature=0.3,
            model="gpt-4-turbo-preview",
            openai_api_key=self.openai_api_key
        )

        # Memory for conversation context
        self.memory_store = {}

    async def initialize(self):
        """Initialize AI engine components"""
        logger.info("AI Engine initialized")

    async def generate_json(self, prompt: str, temperature: float = 0.3) -> Dict[str, Any]:
        """
        Generate structured JSON response from prompt
        """
        try:
            messages = [
                SystemMessage(content="You are an intelligent assistant that always responds with valid JSON."),
                HumanMessage(content=prompt)
            ]

            response = await self.llm.ainvoke(messages, temperature=temperature)

            # Parse JSON from response
            json_str = response.content
            if "```json" in json_str:
                json_str = json_str.split("```json")[1].split("```")[0]
            elif "```" in json_str:
                json_str = json_str.split("```")[1].split("```")[0]

            return json.loads(json_str.strip())
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse JSON: {e}")
            return {}
        except Exception as e:
            logger.error(f"Error generating JSON: {e}")
            return {}

    async def analyze_transcript(self, transcript: str) -> Dict[str, Any]:
        """
        Analyze transcript chunk for real-time insights
        """
        try:
            prompt = f"""
            Analyze this conversation transcript and extract:
            1. Key topics discussed
            2. Customer sentiment (positive/neutral/negative)
            3. Any commitments or promises made
            4. Action items mentioned
            5. Urgency level (low/medium/high)

            Transcript:
            {transcript}

            Respond in JSON format.
            """

            return await self.generate_json(prompt)
        except Exception as e:
            logger.error(f"Error analyzing transcript: {e}")
            return {
                "topics": [],
                "sentiment": "neutral",
                "commitments": [],
                "action_items": [],
                "urgency": "low"
            }

    async def generate_call_summary(
        self,
        transcript: str,
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Generate comprehensive call summary
        """
        try:
            caller_type = context.get('caller_type', 'unknown')
            contact_name = context.get('contact_data', {}).get('name', 'Unknown Caller')
            captured_info = context.get('captured_info', {})

            prompt = f"""
            Generate a comprehensive summary of this after-hours call.

            Caller Type: {caller_type}
            Caller Name: {contact_name}
            Call Duration: {context.get('duration', 'unknown')}

            Full Transcript:
            {transcript}

            Captured Information:
            {json.dumps(captured_info, indent=2)}

            Provide:
            1. Executive summary (2-3 sentences)
            2. Main points discussed
            3. Customer needs identified
            4. Commitments made by either party
            5. Follow-up actions required
            6. Sentiment analysis
            7. Urgency level
            8. Recommended next steps

            Format as JSON.
            """

            summary = await self.generate_json(prompt, temperature=0.2)

            # Add metadata
            summary['generated_at'] = datetime.utcnow().isoformat()
            summary['call_id'] = context.get('call_id')
            summary['phone'] = context.get('phone')

            return summary
        except Exception as e:
            logger.error(f"Error generating call summary: {e}")
            return {
                "executive_summary": "Call summary generation failed",
                "main_points": [],
                "customer_needs": [],
                "commitments": [],
                "follow_ups": [],
                "sentiment": "unknown",
                "urgency": "medium",
                "next_steps": ["Manual review required"]
            }

    async def generate_response(
        self,
        context: str,
        user_input: str,
        conversation_history: List[Dict] = None
    ) -> str:
        """
        Generate contextual response for conversation
        """
        try:
            messages = [
                SystemMessage(content=f"""
                You are Amber, ClearVC's after-hours assistant.
                You are professional, helpful, and empathetic.
                Current context: {context}
                """)
            ]

            # Add conversation history if available
            if conversation_history:
                for msg in conversation_history[-5:]:  # Last 5 messages
                    if msg['role'] == 'user':
                        messages.append(HumanMessage(content=msg['content']))
                    else:
                        messages.append(AIMessage(content=msg['content']))

            # Add current input
            messages.append(HumanMessage(content=user_input))

            response = await self.llm.ainvoke(messages, temperature=0.7)
            return response.content
        except Exception as e:
            logger.error(f"Error generating response: {e}")
            return "I understand. Let me help you with that."

    async def classify_intent(self, text: str) -> Dict[str, Any]:
        """
        Classify the intent of user input
        """
        try:
            prompt = f"""
            Classify the intent of this message:
            "{text}"

            Possible intents:
            - schedule_appointment
            - get_information
            - report_issue
            - speak_to_human
            - check_status
            - general_inquiry
            - emergency

            Also determine:
            - Urgency (low/medium/high/critical)
            - Requires human (yes/no)
            - Category (sales/support/billing/general)

            Respond in JSON format.
            """

            return await self.generate_json(prompt)
        except Exception as e:
            logger.error(f"Error classifying intent: {e}")
            return {
                "intent": "general_inquiry",
                "urgency": "medium",
                "requires_human": False,
                "category": "general"
            }

    async def extract_entities(self, text: str) -> Dict[str, Any]:
        """
        Extract entities from text (names, dates, phone numbers, etc.)
        """
        try:
            prompt = f"""
            Extract all entities from this text:
            "{text}"

            Extract:
            - Names (person names)
            - Phone numbers
            - Email addresses
            - Dates and times
            - Company names
            - Monetary amounts
            - Locations

            Respond in JSON format.
            """

            return await self.generate_json(prompt)
        except Exception as e:
            logger.error(f"Error extracting entities: {e}")
            return {}

    async def generate_follow_up_tasks(
        self,
        summary: Dict[str, Any],
        contact_data: Dict[str, Any] = None
    ) -> List[Dict[str, Any]]:
        """
        Generate follow-up tasks based on call summary
        """
        try:
            prompt = f"""
            Based on this call summary, generate specific follow-up tasks:

            Summary:
            {json.dumps(summary, indent=2)}

            Contact Information:
            {json.dumps(contact_data, indent=2) if contact_data else 'New contact'}

            Generate tasks with:
            - title: Brief task description
            - description: Detailed task requirements
            - due_date: When it should be completed (ISO format)
            - priority: high/medium/low
            - type: callback/email/appointment/internal

            Respond with a JSON array of tasks.
            """

            result = await self.generate_json(prompt)
            return result if isinstance(result, list) else result.get('tasks', [])
        except Exception as e:
            logger.error(f"Error generating follow-up tasks: {e}")
            return []

    async def use_cloudflare_ai(
        self,
        prompt: str,
        model: str = "@cf/meta/llama-2-7b-chat-int8"
    ) -> str:
        """
        Use Cloudflare AI as alternative/fallback
        """
        try:
            url = f"https://api.cloudflare.com/client/v4/accounts/{self.cloudflare_account_id}/ai/run/{model}"

            headers = {
                "Authorization": f"Bearer {self.cloudflare_api_token}",
                "Content-Type": "application/json"
            }

            async with httpx.AsyncClient() as client:
                response = await client.post(
                    url,
                    headers=headers,
                    json={
                        "prompt": prompt,
                        "max_tokens": 500
                    }
                )

                if response.status_code == 200:
                    result = response.json()
                    return result.get('result', {}).get('response', '')
                else:
                    logger.error(f"Cloudflare AI error: {response.text}")
                    return ""
        except Exception as e:
            logger.error(f"Error using Cloudflare AI: {e}")
            return ""

    async def generate_email_content(
        self,
        summary: Dict[str, Any],
        recipient_type: str = "customer"
    ) -> Dict[str, str]:
        """
        Generate email content for follow-ups
        """
        try:
            prompt = f"""
            Generate a professional follow-up email based on this call summary:

            Summary:
            {json.dumps(summary, indent=2)}

            Recipient: {recipient_type}

            Provide:
            - subject: Email subject line
            - body: Full email body (professional, friendly tone)

            Format as JSON.
            """

            return await self.generate_json(prompt)
        except Exception as e:
            logger.error(f"Error generating email: {e}")
            return {
                "subject": "Follow-up from your recent call with ClearVC",
                "body": "Thank you for calling ClearVC. We've noted your inquiry and will follow up soon."
            }

    async def check_escalation_needed(
        self,
        transcript: str,
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Determine if escalation to human is needed
        """
        try:
            prompt = f"""
            Analyze if this conversation needs human escalation:

            Transcript:
            {transcript}

            Context:
            - Caller Type: {context.get('caller_type')}
            - Call Duration: {context.get('duration_seconds', 0)} seconds

            Check for:
            - Frustration or anger
            - Complex technical issues
            - VIP customer needs
            - Emergency situations
            - Repeated requests for human
            - Inability to resolve issue

            Respond with:
            - needs_escalation: true/false
            - reason: why escalation is needed
            - urgency: low/medium/high/critical
            - suggested_department: sales/support/technical/management

            Format as JSON.
            """

            return await self.generate_json(prompt)
        except Exception as e:
            logger.error(f"Error checking escalation: {e}")
            return {
                "needs_escalation": False,
                "reason": "Unable to determine",
                "urgency": "medium",
                "suggested_department": "support"
            }
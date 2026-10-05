import os
import json
import logging
from typing import Dict, Any, Tuple, Optional
from datetime import datetime

# Configure module logger
logger = logging.getLogger("foundry_service")
logger.setLevel(logging.INFO)

class MicrosoftFoundryService:
    """
    Dedicated service for integrating with Microsoft Foundry (Azure AI Foundry / Studio).
    Handles authentication, payload formatting, SDK invocation, and error handling.
    """

    def __init__(
        self,
        endpoint: Optional[str] = None,
        api_key: Optional[str] = None,
        deployment_name: Optional[str] = None,
        api_version: Optional[str] = None
    ):
        self.endpoint = (endpoint or os.getenv("FOUNDRY_ENDPOINT", "")).strip()
        self.api_key = (api_key or os.getenv("FOUNDRY_API_KEY", "")).strip()
        self.deployment_name = (deployment_name or os.getenv("FOUNDRY_DEPLOYMENT_NAME", "")).strip()
        self.api_version = (api_version or os.getenv("FOUNDRY_API_VERSION", "2024-06-01")).strip()

    def validate_configuration(self) -> Tuple[bool, Optional[str]]:
        """
        Verify that Microsoft Foundry configuration credentials are valid and not placeholders.
        """
        placeholders = {
            "YOUR_MICROSOFT_FOUNDRY_ENDPOINT",
            "YOUR_MICROSOFT_FOUNDRY_API_KEY",
            "YOUR_DEPLOYMENT_NAME",
            "YOUR_API_VERSION",
            ""
        }

        if not self.endpoint or self.endpoint in placeholders:
            return False, "FOUNDRY_ENDPOINT is not configured in .env"
        if not self.api_key or self.api_key in placeholders:
            return False, "FOUNDRY_API_KEY is not configured in .env"
        if not self.deployment_name or self.deployment_name in placeholders:
            return False, "FOUNDRY_DEPLOYMENT_NAME is not configured in .env"

        return True, None

    def _call_foundry_model(self, system_prompt: str, user_prompt: str) -> Dict[str, Any]:
        """
        Execute request against Microsoft Foundry using the official SDK or OpenAI-compatible client.
        Gracefully catches network, authorization, and model execution failures.
        """
        is_valid, error_message = self.validate_configuration()
        if not is_valid:
            logger.warning(f"Microsoft Foundry invocation rejected: {error_message}")
            return {
                "success": False,
                "error": f"Microsoft Foundry is not configured: {error_message}. Please update your .env file with valid Azure AI Foundry credentials."
            }

        # 1. Primary: OpenAI / Azure OpenAI v1 client (matches https://...openai.azure.com/openai/v1)
        try:
            from openai import OpenAI, AzureOpenAI
            
            # If endpoint is Azure OpenAI /openai/v1 endpoint (standard in Azure AI Foundry)
            if "/openai/v1" in self.endpoint or self.endpoint.endswith("/v1"):
                client = OpenAI(
                    base_url=self.endpoint,
                    api_key=self.api_key
                )
                response = client.chat.completions.create(
                    model=self.deployment_name,
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt}
                    ],
                    temperature=0.3,
                    max_tokens=1500
                )
                content = response.choices[0].message.content
                return {"success": True, "response": content}
            
            # If base Azure OpenAI endpoint
            elif "openai.azure.com" in self.endpoint:
                clean_endpoint = self.endpoint.split("/openai")[0].rstrip("/")
                client = AzureOpenAI(
                    azure_endpoint=clean_endpoint,
                    api_key=self.api_key,
                    api_version=self.api_version
                )
                response = client.chat.completions.create(
                    model=self.deployment_name,
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt}
                    ],
                    temperature=0.3,
                    max_tokens=1500
                )
                content = response.choices[0].message.content
                return {"success": True, "response": content}

        except Exception as openai_err:
            logger.warning(f"OpenAI client call returned: {openai_err}. Trying azure-ai-inference SDK...")

        # 2. Azure AI Inference SDK (matches https://...services.ai.azure.com/models)
        try:
            from azure.ai.inference import ChatCompletionsClient
            from azure.ai.inference.models import SystemMessage, UserMessage
            from azure.core.credentials import AzureKeyCredential

            # Clean endpoint for azure-ai-inference
            endpoint_url = self.endpoint
            if "/openai/v1" in endpoint_url:
                endpoint_url = endpoint_url.replace("/openai/v1", "/models")

            client = ChatCompletionsClient(
                endpoint=endpoint_url,
                credential=AzureKeyCredential(self.api_key)
            )

            messages = [
                SystemMessage(content=system_prompt),
                UserMessage(content=user_prompt)
            ]

            response = client.complete(
                messages=messages,
                model=self.deployment_name,
                temperature=0.3,
                max_tokens=1500
            )

            content = response.choices[0].message.content
            return {"success": True, "response": content}

        except Exception as sdk_err:
            logger.warning(f"azure-ai-inference SDK returned: {sdk_err}. Trying direct HTTP request...")

        # 3. Direct HTTP request fallback to Foundry REST API
        try:
            import requests

            headers = {
                "Content-Type": "application/json",
                "api-key": self.api_key,
                "Authorization": f"Bearer {self.api_key}"
            }

            # Check if URL already has path
            url = self.endpoint.rstrip("/")
            if "/chat/completions" not in url:
                if "openai.azure.com" in url:
                    url = f"{url}/openai/deployments/{self.deployment_name}/chat/completions?api-version={self.api_version}"
                elif "/models" in url:
                    url = f"{url}/chat/completions"
                else:
                    url = f"{url}/chat/completions"

            payload = {
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                "model": self.deployment_name,
                "temperature": 0.3,
                "max_tokens": 1500
            }

            resp = requests.post(url, headers=headers, json=payload, timeout=30)
            if resp.status_code == 200:
                data = resp.json()
                content = data["choices"][0]["message"]["content"]
                return {"success": True, "response": content}
            else:
                logger.error(f"Foundry REST error HTTP {resp.status_code}: {resp.text}")
                return {
                    "success": False,
                    "error": f"Microsoft Foundry API returned error HTTP {resp.status_code}: {resp.text}"
                }

        except Exception as e:
            logger.error(f"Microsoft Foundry connection failure: {str(e)}", exc_info=True)
            return {
                "success": False,
                "error": f"AI service is currently unavailable. Failed to reach Microsoft Foundry: {str(e)}"
            }

    def chat(self, user_message: str, inventory_context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Interactive Q&A assistant for inventory management with contextual SQLite data.
        """
        system_prompt = (
            "You are the 'Inventory Intelligence Assistant', an AI advisor integrated directly "
            "into the enterprise inventory monitor via Microsoft Foundry.\n"
            "You have direct access to the live SQLite inventory database context provided below.\n"
            "Analyze the database facts accurately, give concise and professional recommendations, "
            "and suggest priority restocking actions when asked.\n\n"
            f"LIVE INVENTORY CONTEXT (JSON):\n{json.dumps(inventory_context, indent=2)}\n\n"
            "Guidelines:\n"
            "1. Base your answer strictly on the real inventory data provided.\n"
            "2. When discussing products, reference their name, current stock, and minimum stock threshold.\n"
            "3. If products are OUT_OF_STOCK or LOW_STOCK, state their urgency clearly.\n"
            "4. Provide well-structured markdown formatting with bullet points or numbered lists."
        )

        user_prompt = f"User Question: {user_message}"
        return self._call_foundry_model(system_prompt, user_prompt)

    def analyze_inventory(self, inventory_context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate a comprehensive inventory analysis and store structured insights in the database.
        """
        system_prompt = (
            "You are the 'Inventory Intelligence Assistant' powered by Microsoft Foundry.\n"
            "Analyze the entire inventory status provided in the JSON context.\n"
            "Your output must contain:\n"
            "1. Executive Inventory Summary (Catalog size, valuation, stock health percentage)\n"
            "2. Critical Stockout & Low-Stock Risks\n"
            "3. Category Vulnerability Assessment\n"
            "4. Prioritized Restocking Recommendations (High, Medium, Low)\n"
            "5. Strategic inventory management suggestions.\n\n"
            f"INVENTORY DATA:\n{json.dumps(inventory_context, indent=2)}"
        )

        user_prompt = (
            "Please perform a complete diagnostic analysis of the current inventory and "
            "recommend immediate operational actions."
        )

        result = self._call_foundry_model(system_prompt, user_prompt)
        if result.get("success"):
            self._record_insights_from_analysis(result["response"], inventory_context)

        return result

    def recommend_restock(self, inventory_context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate targeted restocking recommendations for at-risk products.
        """
        system_prompt = (
            "You are the 'Inventory Intelligence Assistant' powered by Microsoft Foundry.\n"
            "Review the items marked as OUT_OF_STOCK or LOW_STOCK in the inventory context.\n"
            "For each problematic item, provide:\n"
            "- Product name and current stock vs minimum stock\n"
            "- Urgency Level: HIGH, MEDIUM, or LOW\n"
            "- Suggested Reorder Quantity (e.g., target 2x or 3x minimum stock)\n"
            "- Rationale (stockout risk, supplier lead-time consideration)\n\n"
            f"INVENTORY DATA:\n{json.dumps(inventory_context, indent=2)}"
        )

        user_prompt = "Generate detailed restocking recommendations for all low-stock and out-of-stock items."

        result = self._call_foundry_model(system_prompt, user_prompt)
        if result.get("success"):
            self._record_insights_from_analysis(result["response"], inventory_context, insight_type="RESTOCK_RECOMMENDATION")

        return result

    def get_inventory_summary(self, inventory_context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate a quick executive summary of the inventory.
        """
        system_prompt = (
            "You are the 'Inventory Intelligence Assistant' powered by Microsoft Foundry.\n"
            "Produce a concise, 2-3 paragraph executive summary of inventory status, "
            "highlighting key metrics, risks, and health status."
        )
        user_prompt = f"Summarize current inventory status based on this data:\n{json.dumps(inventory_context, indent=2)}"
        return self._call_foundry_model(system_prompt, user_prompt)

    def _record_insights_from_analysis(
        self,
        analysis_text: str,
        inventory_context: Dict[str, Any],
        insight_type: str = "INVENTORY_ANALYSIS"
    ) -> None:
        """
        Save parsed recommendations into the SQLite database ai_insights table.
        """
        try:
            from models import db, AIInsight, Product

            # Create an overall analysis insight record
            summary_insight = AIInsight(
                product_id=None,
                insight_type=insight_type,
                recommendation=analysis_text[:2000],  # Truncate if extremely long for summary
                priority="HIGH" if inventory_context.get("out_of_stock_items") else "MEDIUM"
            )
            db.session.add(summary_insight)

            # Also create product-specific insights for out of stock / low stock items
            out_of_stock = inventory_context.get("out_of_stock_items", [])
            for item in out_of_stock[:3]:
                db.session.add(AIInsight(
                    product_id=item["id"],
                    insight_type="RISK_ALERT",
                    recommendation=f"CRITICAL: '{item['name']}' is completely OUT OF STOCK (0 units). Reorder immediately to avoid lost sales.",
                    priority="HIGH"
                ))

            low_stock = inventory_context.get("low_stock_items", [])
            for item in low_stock[:3]:
                db.session.add(AIInsight(
                    product_id=item["id"],
                    insight_type="RESTOCK_RECOMMENDATION",
                    recommendation=f"WARNING: '{item['name']}' is LOW ON STOCK ({item['current_stock']} units remaining, min: {item['min_stock']}). Restock recommended.",
                    priority="MEDIUM"
                ))

            db.session.commit()
            logger.info("Successfully recorded AI insights to SQLite database.")
        except Exception as e:
            logger.error(f"Failed to record AI insights to database: {e}")

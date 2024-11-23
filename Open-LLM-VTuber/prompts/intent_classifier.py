from enum import Enum
from typing import Dict, Any, Tuple

class MessageIntent(Enum):
    CRYPTO_TIP = "crypto_tip"
    INVESTOR_RELATIONS = "investor_relations"
    GENERAL_CHAT = "general_chat"
    TECHNICAL_SUPPORT = "technical_support"

async def classify_message(message: str, llm_client: Any) -> Tuple[MessageIntent, float]:
    """
    Classify incoming message intent using the LLM.
    Returns tuple of (intent, confidence_score)
    """
    classification_prompt = f"""
    Classify the following message into one of these categories:
    - INVESTOR_RELATIONS: Questions about token metrics, market cap, trading pairs, liquidity, or project roadmap
    - TECHNICAL_SUPPORT: Technical issues or how-to questions
    - GENERAL_CHAT: General conversation or greetings
    
    Message: {message}
    
    Respond with only the category name and confidence score (0-1), separated by |
    """
    
    response = await llm_client.generate(classification_prompt)
    category, confidence = response.strip().split("|")
    return MessageIntent(category.strip()), float(confidence) 
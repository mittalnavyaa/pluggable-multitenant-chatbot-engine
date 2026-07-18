import re
from abc import ABC, abstractmethod

class IntentClassifier(ABC):
    """Abstract interface defining the contract for lightweight conversational intent classification."""
    
    @abstractmethod
    def classify(self, message: str) -> str:
        """
        Classifies the incoming message content.
        
        Returns:
            "conversational" or "knowledge"
        """
        pass

class DefaultIntentClassifier(IntentClassifier):
    """Default lightweight pattern and keyword matching implementation."""
    
    def __init__(self) -> None:
        # Predefined phrases (exact matching after normalization and trailing punctuation cleanup)
        self.conversational_phrases = {
            "hi", "hello", "hey", "yo", "greetings", "howdy", "hola",
            "thanks", "thank you", "thank you very much", "thanks a lot", "appreciate it",
            "bye", "goodbye", "see you", "see ya", "talk to you later", "farewell",
            "who are you", "what can you do", "help", "what is your name",
            "good morning", "good afternoon", "good evening", "good day",
            "hi there", "hello there", "hey there", "see you later", "many thanks", "thank you so much"
        }

    def classify(self, message: str) -> str:
        if not message or not isinstance(message, str):
            return "knowledge"
            
        # 1. Basic cleaning and normalization
        normalized = message.lower().strip()
        
        # Strip leading/trailing non-alphanumeric/non-space characters (punctuation)
        cleaned = re.sub(r'^[^\w\s]+|[^\w\s]+$', '', normalized).strip()
        
        if not cleaned:
            return "knowledge"
            
        # 2. Exact match check
        if cleaned in self.conversational_phrases:
            return "conversational"
            
        return "knowledge"

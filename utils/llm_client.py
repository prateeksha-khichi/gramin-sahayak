"""
LLM Client - Handles Groq API calls (FREE tier)
Groq provides fast inference with generous free limits
"""

import os
from typing import Optional
from groq import Groq
from loguru import logger


class LLMClient:
    """
    Groq API client for text generation
    FREE tier: 14,400 requests/day, 20 requests/minute
    """
    
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv('GROQ_API_KEY')
        
        if not self.api_key:
            logger.warning("⚠️ GROQ_API_KEY not found! LLM features will not work.")
            self.client = None
        else:
            self.client = Groq(api_key=self.api_key)
            logger.info("✅ Groq client initialized")
        
        # Default model - llama3 is fast and good for Hindi/English
        self.model = "llama-3.1-8b-instant"  # or "mixtral-8x7b-32768"
    
    def generate(self, 
                 prompt: str, 
                 max_tokens: int = 500,
                 temperature: float = 0.3,
                 system_prompt: Optional[str] = None) -> str:
        """
        Generate response from prompt
        
        Args:
            prompt: User prompt
            max_tokens: Maximum response length
            temperature: Creativity (0-1, lower = more focused)
            system_prompt: Optional system instruction
        
        Returns:
            Generated text
        """
        if not self.client:
            return "⚠️ LLM सेवा उपलब्ध नहीं है। कृपया API कुंजी जांचें।"
        
        try:
            messages = []
            
            if system_prompt:
                messages.append({
                    "role": "system",
                    "content": system_prompt
                })
            
            messages.append({
                "role": "user",
                "content": prompt
            })
            
            # Call Groq API
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                max_tokens=max_tokens,
                temperature=temperature,
                top_p=0.9,
            )
            
            answer = response.choices[0].message.content.strip()
            
            logger.info(f"✅ Generated response ({len(answer)} chars)")
            return answer
            
        except Exception as e:
            logger.error(f"❌ Groq API error: {e}")
            return f"क्षमा करें, कुछ गलती हुई। कृपया फिर से प्रयास करें। Error: {str(e)}"
    
    def generate_with_retry(self, prompt: str, max_retries: int = 2, **kwargs) -> str:
        """
        Generate with automatic retry on failure
        """
        for attempt in range(max_retries + 1):
            try:
                return self.generate(prompt, **kwargs)
            except Exception as e:
                if attempt < max_retries:
                    logger.warning(f"⚠️ Retry {attempt + 1}/{max_retries}")
                    continue
                else:
                    logger.error(f"❌ All retries failed: {e}")
                    return "क्षमा करें, सेवा अभी उपलब्ध नहीं है। बाद में प्रयास करें।"


# Test
if __name__ == "__main__":
    client = LLMClient()
    
    test_prompt = """प्रधानमंत्री मुद्रा योजना क्या है? सरल हिंदी में 3 वाक्यों में बताओ।"""
    
    response = client.generate(test_prompt, max_tokens=200)
    print(f"Response:\n{response}")
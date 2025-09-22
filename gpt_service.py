import asyncio
from typing import Optional
from openai import AsyncOpenAI
from config import settings


class GPTService:
    
    def __init__(self):
        self.client = AsyncOpenAI(api_key=settings.openai.API_KEY)
        self.model = settings.openai.MODEL
        self.max_tokens = settings.openai.MAX_TOKENS
        self.temperature = settings.openai.TEMPERATURE
    
    async def generate_interpretation(self, card: str, question: str) -> str:
        if not settings.openai.API_KEY:
            return self._get_fallback_interpretation(card)
        
        try:
            prompt = self._build_interpretation_prompt(card, question)
            
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": "Ты опытный таролог с глубокими знаниями карт Таро. Твоя задача - дать точное и полезное толкование карты в контексте вопроса клиента. Отвечай на русском языке, будь мудрым и поддерживающим."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                max_tokens=self.max_tokens,
                temperature=self.temperature
            )
            
            return response.choices[0].message.content.strip()
            
        except Exception as e:
            print(f"Error generating interpretation: {e}")
            return self._get_fallback_interpretation(card)
    
    async def generate_advice(self, card: str, question: str) -> str:
        if not settings.openai.API_KEY:
            return self._get_fallback_advice()
        
        try:
            prompt = self._build_advice_prompt(card, question)
            
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": "Ты мудрый советчик, который помогает людям принимать правильные решения. На основе карты Таро и вопроса клиента дай практический и мудрый совет. Отвечай на русском языке, будь конкретным и поддерживающим."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                max_tokens=self.max_tokens,
                temperature=self.temperature
            )
            
            return response.choices[0].message.content.strip()
            
        except Exception as e:
            print(f"Error generating advice: {e}")
            return self._get_fallback_advice()
    
    def _build_interpretation_prompt(self, card: str, question: str) -> str:
        return f"""
Карта: {card}
Вопрос клиента: {question}

Дай подробное толкование карты {card} в контексте вопроса клиента. 
Объясни, что означает эта карта для данной ситуации, какие энергии она несет, 
и как она может помочь в решении вопроса.
"""
    
    def _build_advice_prompt(self, card: str, question: str) -> str:
        return f"""
Карта: {card}
Вопрос клиента: {question}

На основе карты {card} и вопроса клиента дай практический совет. 
Что нужно делать, как действовать, на что обратить внимание. 
Будь конкретным и полезным.
"""
    
    def _get_fallback_interpretation(self, card: str) -> str:
        return f"Карта {card} указывает на важные изменения в вашей жизни. Звезды советуют быть внимательными к знакам судьбы и доверять своей интуиции."
    
    def _get_fallback_advice(self) -> str:
        return "Сейчас самое время для новых начинаний. Доверьтесь своему внутреннему голосу и не бойтесь перемен."

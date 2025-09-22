import random
from typing import Optional
from dataclasses import asdict
from db.models import User, TarotReading, DeckType
from interfaces import IUserRepository, ITarotService, IUserService, IMessageService
from validators import SecurityValidator
from cache import CacheManager
from messages import BotMessages
from gpt_service import GPTService


class TarotService(ITarotService):
    
    def __init__(self, tarot_config, validator: SecurityValidator = None, cache_manager: CacheManager = None, gpt_service: GPTService = None):
        self.tarot_config = tarot_config
        self._validator = validator or SecurityValidator()
        self._cache_manager = cache_manager
        self._gpt_service = gpt_service or GPTService()
    
    async def get_random_card(self, deck_type: DeckType) -> str:
        if not isinstance(deck_type, DeckType):
            raise ValueError(f"Invalid deck type: {deck_type}")
        
        try:
            cache_key = f"tarot_cards:{deck_type.value}"
            if self._cache_manager:
                cached_cards = await self._cache_manager.get(cache_key)
                if cached_cards:
                    card = random.choice(cached_cards)
                    return card

            if deck_type == DeckType.RIDER_WAITE:
                cards = self.tarot_config.rider_waite_cards
            else:
                cards = self.tarot_config.lenormand_cards
            
            if not cards:
                raise ValueError(f"No cards available for deck type: {deck_type}")
            
            if self._cache_manager:
                await self._cache_manager.set(cache_key, cards, ttl=3600)
            
            card = random.choice(cards)
            return card
        except Exception as e:
            raise
    
    async def create_reading(self, user_id: int, question: str, deck_type: str = "rider_waite") -> TarotReading:
        if not self._validator.validate_message_text(question):
            raise ValueError("Invalid question text")
        
        try:
            card = await self.get_random_card(deck_type)
            sanitized_question = self._validator.sanitize_text(question)
            
            interpretation = await self._generate_interpretation(card, sanitized_question)
            advice = await self._generate_advice(card, sanitized_question)
            
            return TarotReading(
                card_name=card,
                question=sanitized_question,
                interpretation=interpretation,
                advice=advice,
                remaining_messages=9
            )
        except Exception as e:
            raise
    
    async def _generate_interpretation(self, card: str, question: str) -> str:
        return await self._gpt_service.generate_interpretation(card, question)
    
    async def _generate_advice(self, card: str, question: str) -> str:
        return await self._gpt_service.generate_advice(card, question)


class UserService(IUserService):
    
    def __init__(
        self, 
        repository: IUserRepository, 
        referral_bonus: int = 10,
        validator: SecurityValidator = None,
        cache_manager: CacheManager = None
    ):
        self.repository = repository
        self.referral_bonus = referral_bonus
        self._validator = validator or SecurityValidator()
        self._cache_manager = cache_manager
    
    async def get_or_create_user(self, user_id: int) -> User:
        if not self._validator.validate_user_id(str(user_id)):
            raise ValueError(f"Invalid user ID: {user_id}")
        
        try:
            cache_key = f"user:{user_id}"
            if self._cache_manager:
                cached_user = await self._cache_manager.get(cache_key)
                if cached_user:
                    return User(**cached_user)
            
            user = await self.repository.get_or_create_user(user_id)
            
            if self._cache_manager:
                await self._cache_manager.set(cache_key, asdict(user), ttl=1800)
            
            return user
        except Exception as e:
            raise
    
    async def can_send_message(self, user_id: int) -> bool:
        if not self._validator.validate_user_id(str(user_id)):
            return False
        
        try:
            user = await self.repository.get_user(user_id)
            return user is not None and user.balance > 0
        except Exception as e:
            return False
    
    async def consume_message(self, user_id: int) -> bool:
        if not self._validator.validate_user_id(str(user_id)):
            return False
        
        try:
            return await self.repository.decrement_balance(user_id)
        except Exception as e:
            return False
    
    async def process_referral(self, new_user_id: int, referrer_id: int) -> bool:
        if not self._validator.validate_user_id(str(new_user_id)):
            return False
        
        if not self._validator.validate_user_id(str(referrer_id)):
            return False
        
        if new_user_id == referrer_id:
            return False
        
        try:
            new_user_success = await self.repository.add_referral_bonus(
                new_user_id, self.referral_bonus
            )
            referrer_success = await self.repository.add_referral_bonus(
                referrer_id, self.referral_bonus
            )
            
            if not (new_user_success and referrer_success):
                return False
            
            referrer = await self.repository.get_user(referrer_id)
            if referrer:
                referrer.referrals.total_referrals += 1
                referrer.referrals.active_referrals += 1
                referrer.referrals.referrals_list.append(str(new_user_id))
                await self.repository.update_user(referrer)
            
            return True
            
        except Exception as e:
            return False
    
    def get_referral_link(self, user_id: int) -> str:
        if not self._validator.validate_user_id(str(user_id)):
            raise ValueError(f"Invalid user ID: {user_id}")
        
        return BotMessages.REFERRAL_LINK_TEMPLATE.format(user_id=user_id)


class MessageService(IMessageService):
    
    def __init__(self, validator: SecurityValidator = None):
        self._validator = validator or SecurityValidator()
    
    def format_welcome_message(self, user: User, user_name: str) -> str:
        if not isinstance(user, User):
            raise ValueError(f"Invalid user object: {type(user)}")
        
        sanitized_name = self._validator.sanitize_text(user_name or 'друг')
        
        return BotMessages.WELCOME_MESSAGE.format(
            name=sanitized_name,
            balance=user.balance
        )
    
    def format_no_messages_message(self) -> str:
        return BotMessages.NO_MESSAGES_MESSAGE
    
    def format_tarot_reading(self, reading: TarotReading) -> str:
        if not isinstance(reading, TarotReading):
            raise ValueError(f"Invalid reading object: {type(reading)}")
        
        return BotMessages.TAROT_READING_MESSAGE.format(
            question=reading.question,
            card=reading.card,
            interpretation=reading.interpretation,
            advice=reading.advice,
            remaining_messages=reading.remaining_messages
        )
    
    def format_referral_message(self, referral_link: str) -> str:
        if not isinstance(referral_link, str) or not referral_link.strip():
            raise ValueError("Invalid referral link")
        
        return BotMessages.REFERRAL_MESSAGE.format(referral_link=referral_link)
    
    def format_invite_message(self, referral_link: str) -> str:
        if not isinstance(referral_link, str) or not referral_link.strip():
            raise ValueError("Invalid referral link")
        
        return BotMessages.INVITE_MESSAGE.format(referral_link=referral_link)


class ServiceFactory:
    
    @staticmethod
    def create_tarot_service(tarot_config, cache_manager=None) -> ITarotService:
        return TarotService(tarot_config, cache_manager=cache_manager)
    
    @staticmethod
    def create_user_service(
        repository: IUserRepository, 
        referral_bonus: int = 10,
        cache_manager=None
    ) -> IUserService:
        return UserService(repository, referral_bonus, cache_manager=cache_manager)
    
    @staticmethod
    def create_message_service() -> IMessageService:
        return MessageService()

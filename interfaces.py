from abc import ABC, abstractmethod
from typing import Optional, List
from db.models import User, TarotReading, DeckType


class IUserRepository(ABC):
    @abstractmethod
    async def get_user(self, user_id: int) -> Optional[User]:
        pass
    
    @abstractmethod
    async def create_user(self, user_id: int, default_balance: int = 10) -> User:
        pass
    
    @abstractmethod
    async def update_user(self, user: User) -> bool:
        pass
    
    @abstractmethod
    async def delete_user(self, user_id: int) -> bool:
        pass


class ITarotService(ABC):
    @abstractmethod
    async def get_random_card(self, deck_type: DeckType) -> str:
        pass
    
    @abstractmethod
    async def create_reading(self, user: User, question: str) -> TarotReading:
        pass


class IUserService(ABC):
    @abstractmethod
    async def get_or_create_user(self, user_id: int) -> User:
        pass
    
    @abstractmethod
    async def can_send_message(self, user_id: int) -> bool:
        pass
    
    @abstractmethod
    async def consume_message(self, user_id: int) -> bool:
        pass
    
    @abstractmethod
    async def process_referral(self, new_user_id: int, referrer_id: int) -> bool:
        pass


class IMessageService(ABC):
    @abstractmethod
    def format_welcome_message(self, user: User, user_name: str) -> str:
        pass
    
    @abstractmethod
    def format_no_messages_message(self) -> str:
        pass
    
    @abstractmethod
    def format_tarot_reading(self, reading: TarotReading) -> str:
        pass
    
    @abstractmethod
    def format_referral_message(self, referral_link: str) -> str:
        pass
    
    @abstractmethod
    def format_invite_message(self, referral_link: str) -> str:
        pass


class ILogger(ABC):
    @abstractmethod
    def info(self, message: str, **kwargs) -> None:
        pass
    
    @abstractmethod
    def error(self, message: str, **kwargs) -> None:
        pass
    
    @abstractmethod
    def warning(self, message: str, **kwargs) -> None:
        pass
    
    @abstractmethod
    def debug(self, message: str, **kwargs) -> None:
        pass


class IValidator(ABC):
    @abstractmethod
    def validate_user_id(self, user_id: str) -> bool:
        pass
    
    @abstractmethod
    def validate_referral_param(self, param: str) -> bool:
        pass
    
    @abstractmethod
    def validate_message_text(self, text: str) -> bool:
        pass

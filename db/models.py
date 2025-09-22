from dataclasses import dataclass
from typing import List, Optional
from enum import Enum
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete
from sqlalchemy.exc import NoResultFound


class DeckType(Enum):
    RIDER_WAITE = "rider_waite"
    LENORMAND = "lenormand"


@dataclass
class UserSettings:
    deck: DeckType = DeckType.RIDER_WAITE
    daily_tip_enabled: bool = False
    daily_tip_time: str = "18:00"


@dataclass
class ReferralData:
    total_referrals: int = 0
    active_referrals: int = 0
    referrals_list: List[str] = None
    
    def __post_init__(self):
        if self.referrals_list is None:
            self.referrals_list = []


@dataclass
class User:
    user_id: int
    balance: int
    settings: UserSettings
    referrals: ReferralData
    
    @classmethod
    def create_new(cls, user_id: int, default_balance: int = 10) -> 'User':
        return cls(
            user_id=user_id,
            balance=default_balance,
            settings=UserSettings(),
            referrals=ReferralData()
        )


@dataclass
class TarotReading:
    card: str
    question: str
    interpretation: str
    advice: str
    remaining_messages: int


class ModelAdmin:
    
    @classmethod
    async def create(cls, session: AsyncSession, **kwargs):
        obj = cls(**kwargs)
        session.add(obj)
        await session.commit()
        await session.refresh(obj)
        return obj
    
    @classmethod
    async def get(cls, session: AsyncSession, **kwargs) -> Optional['ModelAdmin']:
        params = [getattr(cls, key) == val for key, val in kwargs.items()]
        query = select(cls).where(*params)
        
        try:
            results = await session.execute(query)
            (result,) = results.one()
            return result
        except NoResultFound:
            return None
    
    @classmethod
    async def exists(cls, session: AsyncSession, **kwargs) -> bool:
        params = [getattr(cls, key) == val for key, val in kwargs.items()]
        query = select(cls.id).where(*params)
        
        try:
            results = await session.execute(query)
            results.one()
            return True
        except NoResultFound:
            return False
    
    async def update(self, session: AsyncSession, **kwargs) -> None:
        await session.execute(
            update(self.__class__).where(self.__class__.id == self.id),
            [kwargs]
        )
        await session.commit()
    
    async def delete(self, session: AsyncSession) -> None:
        await session.delete(self)
        await session.commit()

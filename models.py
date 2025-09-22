from dataclasses import dataclass
from typing import List
from enum import Enum


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

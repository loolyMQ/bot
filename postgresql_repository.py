from typing import Dict, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete
from sqlalchemy.exc import IntegrityError

from db.models import User, UserSettings, ReferralData
from interfaces import IUserRepository
from validators import SecurityValidator
from core.database import UserModel


class PostgreSQLUserRepository(IUserRepository):

    def __init__(self, validator: SecurityValidator = None, db_manager=None):
        self._validator = validator or SecurityValidator()
        self._db_manager = db_manager

    async def _get_session(self) -> AsyncSession:
        return await self._db_manager.get_session()

    async def get_user(self, user_id: int) -> Optional[User]:
        if not isinstance(user_id, int) or user_id <= 0:
            return None
            
        if not self._validator.validate_user_id(str(user_id)):
            return None

        try:
            async with await self._get_session() as session:
                stmt = select(UserModel).where(UserModel.user_id == user_id)
                result = await session.execute(stmt)
                user_model = result.scalar_one_or_none()
                
                if user_model:
                    return self._model_to_user(user_model)
                return None
                
        except Exception as e:
            return None

    async def create_user(self, user_id: int, default_balance: int = 10) -> User:
        if not isinstance(user_id, int) or user_id <= 0:
            raise ValueError(f"Invalid user ID type or value: {user_id}")
            
        if not self._validator.validate_user_id(str(user_id)):
            raise ValueError(f"Invalid user ID format: {user_id}")

        if not isinstance(default_balance, int) or default_balance < 0 or default_balance > 10000:
            raise ValueError(f"Invalid default balance: {default_balance}")

        try:
            user = User.create_new(user_id, default_balance)
            user_model = self._user_to_model(user)
            
            async with await self._get_session() as session:
                session.add(user_model)
                await session.commit()
                await session.refresh(user_model)
                
            return user
            
        except IntegrityError:
            return await self.get_user(user_id)
        except Exception as e:
            raise

    async def update_user(self, user: User) -> bool:
        if not isinstance(user, User):
            return False

        if not self._validator.validate_user_id(str(user.user_id)):
            return False

        try:
            async with await self._get_session() as session:
                await session.execute(
                    update(UserModel)
                    .where(UserModel.user_id == user.user_id)
                    .values(
                        balance=user.balance,
                        settings=self._settings_to_dict(user.settings),
                        referrals=self._referrals_to_dict(user.referrals)
                    )
                )
                await session.commit()
                
            return True
            
        except Exception as e:
            return False

    async def delete_user(self, user_id: int) -> bool:
        if not self._validator.validate_user_id(str(user_id)):
            return False

        try:
            async with await self._get_session() as session:
                result = await session.execute(
                    delete(UserModel).where(UserModel.user_id == user_id)
                )
                await session.commit()
                
                if result.rowcount > 0:
                    return True
                return False
                
        except Exception as e:
            return False

    async def get_or_create_user(self, user_id: int, default_balance: int = 10) -> User:
        user = await self.get_user(user_id)
        if user is None:
            user = await self.create_user(user_id, default_balance)
        return user

    async def update_balance(self, user_id: int, new_balance: int) -> bool:
        if not isinstance(new_balance, int) or new_balance < 0:
            return False

        try:
            async with await self._get_session() as session:
                await session.execute(
                    update(UserModel)
                    .where(UserModel.user_id == user_id)
                    .values(balance=new_balance)
                )
                await session.commit()
                return True
                
        except Exception as e:
            return False

    async def decrement_balance(self, user_id: int) -> bool:
        try:
            async with await self._get_session() as session:
                result = await session.execute(
                    update(UserModel)
                    .where(UserModel.user_id == user_id, UserModel.balance > 0)
                    .values(balance=UserModel.balance - 1)
                )
                await session.commit()
                return result.rowcount > 0
                
        except Exception as e:
            return False

    async def add_referral_bonus(self, user_id: int, bonus: int) -> bool:
        if not isinstance(bonus, int) or bonus < 0:
            return False

        try:
            async with await self._get_session() as session:
                await session.execute(
                    update(UserModel)
                    .where(UserModel.user_id == user_id)
                    .values(balance=UserModel.balance + bonus)
                )
                await session.commit()
                return True
                
        except Exception as e:
            return False

    async def update_deck(self, user_id: int, deck_type: str) -> bool:
        if not isinstance(user_id, int) or user_id <= 0:
            return False
            
        if not isinstance(deck_type, str) or not deck_type.strip():
            return False

        allowed_decks = ['rider_waite', 'lenormand']
        if deck_type not in allowed_decks:
            return False

        try:
            async with await self._get_session() as session:
                stmt = select(UserModel).where(UserModel.user_id == user_id)
                result = await session.execute(stmt)
                user_model = result.scalar_one_or_none()
                
                if user_model:
                    settings = user_model.settings or {}
                    settings['deck'] = deck_type
                    
                    update_stmt = (
                        update(UserModel)
                        .where(UserModel.user_id == user_id)
                        .values(settings=settings)
                    )
                    await session.execute(update_stmt)
                    await session.commit()
                    return True
                return False
                
        except Exception as e:
            return False

    async def update_daily_tip_settings(
        self, user_id: int, enabled: bool, time: str
    ) -> bool:
        if not isinstance(user_id, int) or user_id <= 0:
            return False
            
        if not isinstance(enabled, bool):
            return False

        if not isinstance(time, str) or not time.strip():
            return False

        import re
        time_pattern = r'^([01]?[0-9]|2[0-3]):[0-5][0-9]$'
        if not re.match(time_pattern, time.strip()):
            return False

        try:
            async with await self._get_session() as session:
                stmt = select(UserModel).where(UserModel.user_id == user_id)
                result = await session.execute(stmt)
                user_model = result.scalar_one_or_none()
                
                if user_model:
                    settings = user_model.settings or {}
                    settings['daily_tip_enabled'] = enabled
                    settings['daily_tip_time'] = time.strip()
                    
                    update_stmt = (
                        update(UserModel)
                        .where(UserModel.user_id == user_id)
                        .values(settings=settings)
                    )
                    await session.execute(update_stmt)
                    await session.commit()
                    return True
                return False
                
        except Exception as e:
            return False

    async def get_user_count(self) -> int:
        try:
            async with await self._get_session() as session:
                result = await session.execute(select(UserModel.user_id))
                return len(result.scalars().all())
                
        except Exception as e:
            return 0

    async def get_all_users(self) -> Dict[int, User]:
        try:
            async with await self._get_session() as session:
                result = await session.execute(select(UserModel))
                users = {}
                for user_model in result.scalars().all():
                    user = self._model_to_user(user_model)
                    users[user.user_id] = user
                return users
                
        except Exception as e:
            return {}

    def _model_to_user(self, model: UserModel) -> User:
        settings_dict = model.settings or {}
        referrals_dict = model.referrals or {}
        
        settings = UserSettings(
            deck=settings_dict.get('deck', 'rider_waite'),
            daily_tip_enabled=settings_dict.get('daily_tip_enabled', False),
            daily_tip_time=settings_dict.get('daily_tip_time', '18:00')
        )
        
        referrals = ReferralData(
            total_referrals=referrals_dict.get('total_referrals', 0),
            active_referrals=referrals_dict.get('active_referrals', 0),
            referrals_list=referrals_dict.get('referrals_list', [])
        )
        
        return User(
            user_id=model.user_id,
            balance=model.balance,
            settings=settings,
            referrals=referrals
        )

    def _user_to_model(self, user: User) -> UserModel:
        return UserModel(
            user_id=user.user_id,
            balance=user.balance,
            settings=self._settings_to_dict(user.settings),
            referrals=self._referrals_to_dict(user.referrals)
        )

    def _settings_to_dict(self, settings: UserSettings) -> Dict:
        return {
            'deck': settings.deck.value,
            'daily_tip_enabled': settings.daily_tip_enabled,
            'daily_tip_time': settings.daily_tip_time
        }

    def _referrals_to_dict(self, referrals: ReferralData) -> Dict:
        return {
            'total_referrals': referrals.total_referrals,
            'active_referrals': referrals.active_referrals,
            'referrals_list': referrals.referrals_list
        }

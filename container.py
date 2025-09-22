from typing import Dict, Any, Type, TypeVar
from interfaces import (
    IUserRepository, ITarotService, IUserService, IMessageService, IValidator
)
from postgresql_repository import PostgreSQLUserRepository
from services import TarotService, UserService, MessageService
from validators import SecurityValidator
from config import settings
from core.database import DatabaseManagerFactory
from cache import CacheManagerFactory
from rate_limiter import RateLimiterFactory
from gpt_service import GPTService

T = TypeVar('T')


class DIContainer:
    def __init__(self):
        self._singletons: Dict[Type, Any] = {}
        self._transients: Dict[Type, Any] = {}
        self._factories: Dict[Type, callable] = {}
        self._initialized = False
        self._db_manager = None
        self._cache_manager = None
        self._rate_limiter = None
    
    def register_singleton(self, interface: Type[T], implementation: Type[T]) -> None:
        self._singletons[interface] = implementation
    
    def register_transient(self, interface: Type[T], implementation: Type[T]) -> None:
        self._transients[interface] = implementation
    
    def register_factory(self, interface: Type[T], factory: callable) -> None:
        self._factories[interface] = factory
    
    def get(self, interface: Type[T]) -> T:
        if interface in self._singletons:
            if isinstance(self._singletons[interface], type):
                self._singletons[interface] = self._singletons[interface]()
            return self._singletons[interface]
        
        if interface in self._transients:
            return self._transients[interface]()
        
        if interface in self._factories:
            return self._factories[interface]()
        
        raise ValueError(f"Dependency not registered: {interface.__name__}")
    
    async def initialize(
        self, 
        database_url: str,
        redis_url: str
    ) -> None:
        if self._initialized:
            return
        
        try:
            self._db_manager = DatabaseManagerFactory.create_database_manager(database_url)
            self._cache_manager = CacheManagerFactory.create_cache_manager(redis_url)
            self._rate_limiter = RateLimiterFactory.create_rate_limiter(redis_url)
            
            await self._db_manager.initialize()
            await self._cache_manager.initialize()
            await self._rate_limiter.initialize()
            
            self.register_singleton(IValidator, SecurityValidator)
            self.register_factory(
                IUserRepository, 
                lambda: PostgreSQLUserRepository(db_manager=self._db_manager)
            )
            
            self.register_factory(
                ITarotService, 
                lambda: TarotService(
                    tarot_config, 
                    cache_manager=self._cache_manager,
                    gpt_service=GPTService()
                )
            )
            self.register_factory(
                IUserService,
                lambda: UserService(
                    self.get(IUserRepository),
                    referral_bonus=10,
                    cache_manager=self._cache_manager
                )
            )
            self.register_factory(IMessageService, MessageService)
            
            self._initialized = True
            
        except Exception as e:
            raise
    
    async def cleanup(self):
        try:
            if self._db_manager:
                await self._db_manager.close()
            if self._cache_manager:
                await self._cache_manager.close()
            if self._rate_limiter:
                await self._rate_limiter.close()
        except Exception as e:
            pass


class ContainerFactory:
    @staticmethod
    async def create_container() -> DIContainer:
        container = DIContainer()
        await container.initialize(
            database_url=settings.database.URL,
            redis_url=settings.redis.URL
        )
        return container

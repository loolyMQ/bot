from datetime import datetime
from sqlalchemy import Column, Integer, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy.dialects.postgresql import JSONB

Base = declarative_base()


class UserModel(Base):
    __tablename__ = "users"
    
    user_id = Column(Integer, primary_key=True, index=True)
    balance = Column(Integer, default=10)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    settings = Column(JSONB, default={})
    referrals = Column(JSONB, default={})


class DatabaseManager:
    
    def __init__(self, database_url: str):
        self.database_url = database_url
        self.engine = None
        self.async_session = None
    
    async def initialize(self):
        try:
            self.engine = create_async_engine(
                self.database_url,
                echo=False,
                pool_size=20,
                max_overflow=30,
                pool_pre_ping=True,
                pool_recycle=1800,
                pool_timeout=30,
                connect_args={
                    "command_timeout": 60,
                    "server_settings": {
                        "application_name": "arcana_bot",
                        "jit": "off"
                    }
                }
            )
            
            self.async_session = sessionmaker(
                self.engine, 
                class_=AsyncSession, 
                expire_on_commit=False
            )
            
            async with self.engine.begin() as conn:
                await conn.run_sync(Base.metadata.create_all)
            
        except Exception as e:
            raise
    
    async def get_session(self) -> AsyncSession:
        if not self.async_session:
            raise RuntimeError("Database not initialized")
        return self.async_session()
    
    async def close(self):
        if self.engine:
            await self.engine.dispose()


class DatabaseManagerFactory:
    
    @staticmethod
    def create_database_manager(database_url: str) -> DatabaseManager:
        db_manager = DatabaseManager(database_url)
        return db_manager

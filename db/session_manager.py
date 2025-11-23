from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
import os
from config.env_vars import load_config
from sqlalchemy.ext.declarative import declarative_base

load_config()
DATABASE_URL = os.getenv("DATABASE_URL")

Base = declarative_base()

class SessionManager:
    def __init__(self, database_url: str = DATABASE_URL, echo: bool = True):
        self.engine = create_async_engine(database_url, echo=echo)
        self.async_session = async_sessionmaker(self.engine, class_=AsyncSession, expire_on_commit=False)
    
    async def get_session(self):
        async with self.async_session() as session:
            yield session

    async def create_tables(self):
        async with self.engine.begin() as conn:
            await conn.run_sync(self.base.metadata.create_all)

    def dispose(self):
        self.engine.dispose()

# create a module-global manager instance for DI usage
session_manager = SessionManager()
get_session = session_manager.get_session
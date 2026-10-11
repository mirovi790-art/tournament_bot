from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase
from config import DB_URL

engine = create_async_engine(DB_URL, echo=False)
SessionLocal = async_sessionmaker(engine, expire_on_commit=False)


class Base(DeclarativeBase):
    pass


async def init_db():
    import models  # noqa
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
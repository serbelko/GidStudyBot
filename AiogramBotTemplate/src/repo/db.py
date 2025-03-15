from typing import Optional
from uuid import uuid4
import uuid
from sqlalchemy.ext.asyncio import AsyncSession
from src.models import PlanORM, Base
from sqlalchemy import select

class PlanRepository:
    def __init__(self, db: AsyncSession):
        self.db = db
        Base.metadata.create_all(db.bind)

    def add_plan(self, user_id: str, text: str, label=str) -> dict:
        plan_id = uuid4()
        new_plan = PlanORM(id=plan_id, user_id=user_id, text=text, label=label)

        self.db.add(new_plan)
        self.db.commit()
        self.db.refresh(new_plan)

        return new_plan.to_dict()

    async def get_plan_by_user_id(self, user_id: str) -> Optional[list]:
        result = self.db.execute(select(PlanORM).where(PlanORM.user_id == user_id)
        )
        plans = result.scalars().all()
        plan_lst = [[plan.label, plan.id] for plan in plans]
        return [len(plan_lst), plan_lst]    
    
    async def get_plan_by_plan_id(self, plan_id: str):
        try:
            # Преобразуем строку в UUID (если поле id имеет тип UUID)
            plan_uuid = uuid.UUID(plan_id)
        except ValueError:
            # Если переданный plan_id не является валидным UUID, можно вернуть None или обработать ошибку
            return None

        result = self.db.execute(
            select(PlanORM).where(PlanORM.id == plan_uuid)
        )
        plan = result.scalars().first()
        if plan is None:
            return None
        
        n = {
            'text': plan.text,
            'user_id': plan.user_id
        }
        return n
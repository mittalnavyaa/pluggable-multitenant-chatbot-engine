from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional, List
import uuid

from src.database.database import SessionLocal
from src.models.bot import Bot
from src.models.internal_product import InternalProduct

router = APIRouter(
    prefix="/api/v1/bots",
    tags=["Bots"]
)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

class BotCreateSchema(BaseModel):
    name: str
    product_id: str
    description: Optional[str] = None

class BotResponseSchema(BaseModel):
    id: str
    name: str
    product_id: str
    description: Optional[str] = None

@router.get("", response_model=List[BotResponseSchema])
def list_bots(db: Session = Depends(get_db)):
    results = db.query(Bot, InternalProduct).join(InternalProduct, Bot.product_id == InternalProduct.id).all()
    
    response = []
    for bot, prod in results:
        response.append(BotResponseSchema(
            id=str(bot.id),
            name=bot.bot_name,
            product_id=prod.product_id,
            description=bot.description
        ))
    return response

@router.post("", response_model=BotResponseSchema)
def create_new_bot(payload: BotCreateSchema, db: Session = Depends(get_db)):
    prod = db.query(InternalProduct).filter(InternalProduct.product_id == payload.product_id).first()
    if not prod:
        product_uuid = uuid.uuid4()
        prod = InternalProduct(
            id=product_uuid,
            product_id=payload.product_id,
            product_name=payload.product_id.capitalize(),
            internal_service_token_hash="default_token_hash_placeholder"
        )
        db.add(prod)
        db.commit()
        db.refresh(prod)
        
    new_bot = Bot(
        id=uuid.uuid4(),
        product_id=prod.id,
        bot_name=payload.name,
        description=payload.description
    )
    db.add(new_bot)
    db.commit()
    db.refresh(new_bot)
    
    return BotResponseSchema(
        id=str(new_bot.id),
        name=new_bot.bot_name,
        product_id=prod.product_id,
        description=new_bot.description
    )

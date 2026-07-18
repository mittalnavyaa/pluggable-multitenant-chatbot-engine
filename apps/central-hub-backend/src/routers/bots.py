from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional, List, Any
import json
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
    ui_theme_config: Optional[Any] = None

class BrandingUpdateSchema(BaseModel):
    colors: Optional[dict] = None
    typography: Optional[dict] = None
    layout: Optional[dict] = None
    assets: Optional[dict] = None
    content: Optional[dict] = None
    featureFlags: Optional[dict] = None
    overflowMenu: Optional[list] = None
    theme: Optional[str] = None

@router.get("", response_model=List[BotResponseSchema])
def list_bots(db: Session = Depends(get_db)):
    results = db.query(Bot, InternalProduct).join(InternalProduct, Bot.product_id == InternalProduct.id).all()
    
    response = []
    for bot, prod in results:
        response.append(BotResponseSchema(
            id=str(bot.id),
            name=bot.bot_name,
            product_id=prod.product_id,
            description=bot.description,
            ui_theme_config=bot.ui_theme_config or {}
        ))
    return response

@router.get("/{bot_id}", response_model=BotResponseSchema)
def get_bot(bot_id: str, db: Session = Depends(get_db)):
    try:
        bot_uuid = uuid.UUID(bot_id)
        bot = db.query(Bot).filter(Bot.id == bot_uuid).first()
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid bot UUID format")
        
    if not bot:
        raise HTTPException(status_code=404, detail="Bot not found")
        
    prod = db.query(InternalProduct).filter(InternalProduct.id == bot.product_id).first()
    prod_id = prod.product_id if prod else ""
    
    return BotResponseSchema(
        id=str(bot.id),
        name=bot.bot_name,
        product_id=prod_id,
        description=bot.description,
        ui_theme_config=bot.ui_theme_config or {}
    )

@router.post("", response_model=BotResponseSchema)
def create_new_bot(payload: BotCreateSchema, db: Session = Depends(get_db)):
    prod = db.query(InternalProduct).filter(InternalProduct.product_id == payload.product_id).first()
    if not prod:
        raise HTTPException(status_code=404, detail="Associated product not found.")
        
    new_bot = Bot(
        id=uuid.uuid4(),
        product_id=prod.id,
        bot_name=payload.name,
        description=payload.description,
        ui_theme_config={}
    )
    db.add(new_bot)
    db.commit()
    db.refresh(new_bot)
    
    return BotResponseSchema(
        id=str(new_bot.id),
        name=new_bot.bot_name,
        product_id=prod.product_id,
        description=new_bot.description,
        ui_theme_config=new_bot.ui_theme_config or {}
    )

@router.get("/{bot_id}/branding")
def get_bot_branding(bot_id: str, db: Session = Depends(get_db)):
    try:
        bot_uuid = uuid.UUID(bot_id)
        bot = db.query(Bot).filter(Bot.id == bot_uuid).first()
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid bot UUID format")
        
    if not bot:
        raise HTTPException(status_code=404, detail="Bot not found")
        
    prod = db.query(InternalProduct).filter(InternalProduct.id == bot.product_id).first()
    
    bot_theme = bot.ui_theme_config or {}
    if isinstance(bot_theme, str):
        try:
            bot_theme = json.loads(bot_theme)
        except Exception:
            bot_theme = {}
            
    prod_theme = {}
    if prod:
        prod_theme = prod.ui_theme_config or {}
        if isinstance(prod_theme, str):
            try:
                prod_theme = json.loads(prod_theme)
            except Exception:
                prod_theme = {}
                
    # Deep merge bot_theme into prod_theme (fallback)
    merged_theme = {**prod_theme}
    for key, val in bot_theme.items():
        if val is not None:
            if isinstance(val, dict) and key in merged_theme and isinstance(merged_theme[key], dict):
                merged_theme[key] = {**merged_theme[key], **val}
            else:
                merged_theme[key] = val
                
    return merged_theme

@router.patch("/{bot_id}/branding", response_model=BotResponseSchema)
def update_bot_branding(bot_id: str, payload: BrandingUpdateSchema, db: Session = Depends(get_db)):
    try:
        bot_uuid = uuid.UUID(bot_id)
        bot = db.query(Bot).filter(Bot.id == bot_uuid).first()
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid bot UUID format")
        
    if not bot:
        raise HTTPException(status_code=404, detail="Bot not found")
        
    current_config = dict(bot.ui_theme_config or {})
    if isinstance(current_config, str):
        try:
            current_config = json.loads(current_config)
        except Exception:
            current_config = {}
            
    payload_dict = payload.dict(exclude_unset=True)
    
    # Deep merge layout/colors/etc.
    for key, val in payload_dict.items():
        if val is not None:
            if isinstance(val, dict) and key in current_config and isinstance(current_config[key], dict):
                current_config[key] = {**current_config[key], **val}
            else:
                current_config[key] = val
                
    bot.ui_theme_config = current_config
    db.commit()
    db.refresh(bot)
    
    prod = db.query(InternalProduct).filter(InternalProduct.id == bot.product_id).first()
    prod_id = prod.product_id if prod else ""
    
    return BotResponseSchema(
        id=str(bot.id),
        name=bot.bot_name,
        product_id=prod_id,
        description=bot.description,
        ui_theme_config=bot.ui_theme_config or {}
    )

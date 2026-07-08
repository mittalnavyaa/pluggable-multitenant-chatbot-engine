from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional, List, Any
import json
import uuid
import secrets
import hashlib

from src.database.database import SessionLocal
from src.models.internal_product import InternalProduct

router = APIRouter(
    prefix="/api/v1/products",
    tags=["Products"]
)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

class ProductResponseSchema(BaseModel):
    id: str
    product_id: str
    name: str
    description: Optional[str] = None
    ui_theme_config: Optional[Any] = None
    created_at: str
    updated_at: str
    service_token: Optional[str] = None

@router.get("", response_model=List[ProductResponseSchema])
def list_products(db: Session = Depends(get_db)):
    results = db.query(InternalProduct).all()
    response = []
    for p in results:
        theme = p.ui_theme_config
        if isinstance(theme, str):
            try:
                theme = json.loads(theme)
            except Exception:
                theme = {}
        elif theme is None:
            theme = {}
            
        response.append(ProductResponseSchema(
            id=str(p.id),
            product_id=p.product_id,
            name=p.product_name,
            description=None,
            ui_theme_config=theme,
            created_at=p.created_at.isoformat(),
            updated_at=p.updated_at.isoformat()
        ))
    return response

@router.get("/{product_id}", response_model=ProductResponseSchema)
def get_product(product_id: str, db: Session = Depends(get_db)):
    p = None
    try:
        val = uuid.UUID(product_id)
        p = db.query(InternalProduct).filter(InternalProduct.id == val).first()
    except ValueError:
        pass
        
    if not p:
        p = db.query(InternalProduct).filter(InternalProduct.product_id == product_id).first()
        
    if not p:
        raise HTTPException(status_code=404, detail="Product not found")
        
    theme = p.ui_theme_config
    if isinstance(theme, str):
        try:
            theme = json.loads(theme)
        except Exception:
            theme = {}
    elif theme is None:
        theme = {}
        
    return ProductResponseSchema(
        id=str(p.id),
        product_id=p.product_id,
        name=p.product_name,
        description=None,
        ui_theme_config=theme,
        created_at=p.created_at.isoformat(),
        updated_at=p.updated_at.isoformat()
    )


class ProductCreateSchema(BaseModel):
    product_id: str
    name: str
    ui_theme_config: Optional[dict] = None

@router.post("", response_model=ProductResponseSchema)
def create_new_product(payload: ProductCreateSchema, db: Session = Depends(get_db)):
    existing = db.query(InternalProduct).filter(InternalProduct.product_id == payload.product_id).first()
    if existing:
        raise HTTPException(status_code=400, detail="Product ID already exists")
        
    raw_token = f"svc_{payload.product_id}_{secrets.token_urlsafe(32)}"
    token_hash = hashlib.sha256(raw_token.encode("utf-8")).hexdigest()
    
    product_uuid = uuid.uuid4()
    new_prod = InternalProduct(
        id=product_uuid,
        product_id=payload.product_id,
        product_name=payload.name,
        internal_service_token_hash=token_hash,
        ui_theme_config=payload.ui_theme_config or {}
    )
    db.add(new_prod)
    db.commit()
    db.refresh(new_prod)
    
    return ProductResponseSchema(
        id=str(new_prod.id),
        product_id=new_prod.product_id,
        name=new_prod.product_name,
        description=None,
        ui_theme_config=new_prod.ui_theme_config or {},
        created_at=new_prod.created_at.isoformat(),
        updated_at=new_prod.updated_at.isoformat(),
        service_token=raw_token
    )

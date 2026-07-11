import os
import sys
import uuid
import hashlib
from sqlalchemy import create_engine, text

def main():
    db_url = os.getenv("DATABASE_URL", "postgresql://chatbot:chatbot123@localhost:5433/chatbot_db")
    engine = create_engine(db_url)
    
    product_uuid = uuid.uuid4()
    bot_uuid = uuid.UUID("f83bd273-9d73-4015-8d5c-8e8867964128")
    
    product_id = "tensor"
    product_name = "Tensor Technologies"
    
    # Generate token hash matching the express-server's .env service token
    raw_token = "svc_tensor_Vp3P1IOAOKqq010gk_erukuSCa4mcfteySN3SnOEZrY"
    token_hash = hashlib.sha256(raw_token.encode("utf-8")).hexdigest()
    
    print("Setting up product and bot in PostgreSQL database...")
    try:
        with engine.connect() as conn:
            # 1. Clean existing records if any
            conn.execute(text("DELETE FROM bots WHERE id = :bot_id"), {"bot_id": bot_uuid})
            conn.execute(text("DELETE FROM internal_products WHERE product_id = :product_id"), {"product_id": product_id})
            
            # 2. Insert internal product
            conn.execute(text("""
                INSERT INTO internal_products (id, product_id, product_name, internal_service_token_hash, ui_theme_config)
                VALUES (:id, :product_id, :product_name, :token_hash, '{}')
            """), {
                "id": product_uuid,
                "product_id": product_id,
                "product_name": product_name,
                "token_hash": token_hash
            })
            print(f"- Product '{product_id}' created successfully (ID: {product_uuid})")
            
            # 3. Insert bot
            conn.execute(text("""
                INSERT INTO bots (id, product_id, bot_name, description, status)
                VALUES (:id, :product_id, :bot_name, :description, 'ACTIVE')
            """), {
                "id": bot_uuid,
                "product_id": product_uuid,
                "bot_name": "Tensor AI Support",
                "description": "Enterprise chatbot for Tensor platform."
            })
            print(f"- Bot created successfully (ID: {bot_uuid})")
            
            # 4. Insert default bot settings
            conn.execute(text("""
                INSERT INTO bot_settings (id, bot_id, llm_model, embedding_model, system_prompt, temperature, top_k, language)
                VALUES (:id, :bot_id, 'llama-3.3-70b-versatile', 'default', 'You are a helpful AI assistant.', 0.7, 5, 'en')
            """), {
                "id": uuid.uuid4(),
                "bot_id": bot_uuid
            })
            print("- Default bot settings created.")
            
            conn.commit()
            print("Database setup completed successfully!")
            
    except Exception as e:
        print(f"Error during database setup: {e}")

if __name__ == "__main__":
    main()

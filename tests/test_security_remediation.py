import io
import os
import sys
import uuid
import hashlib
from fastapi.testclient import TestClient
from sqlalchemy import text

current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir)
backend_path = os.path.join(project_root, 'apps', 'central-hub-backend')
if backend_path not in sys.path:
    sys.path.insert(0, backend_path)

if 'src' in sys.modules:
    del sys.modules['src']

from src.main import app
from src.database.database import SessionLocal
from src.models.internal_product import InternalProduct
from src.models.bot import Bot
from src.models.document_registry import DocumentRegistry
from src.init_qdrant import qdrant_client, QDRANT_COLLECTION

client = TestClient(app)

def test_security_remediation_suite():
    db = SessionLocal()
    
    # 1. Test API Token authentication middleware
    resp = client.get('/api/v1/bots')
    assert resp.status_code == 401
    assert 'Missing or invalid Authorization header' in resp.json()['detail']
    
    resp = client.get('/api/v1/bots', headers={'Authorization': 'Bearer invalid_token'})
    assert resp.status_code == 401
    assert 'Invalid or unauthorized service token' in resp.json()['detail']
    
    product_id = f'test_prod_{uuid.uuid4()}'
    resp = client.post('/api/v1/products', json={'product_id': product_id, 'name': 'Test Product'})
    assert resp.status_code == 200
    res_data = resp.json()
    service_token = res_data['service_token']
    product_uuid = res_data['id']
    
    auth_headers = {'Authorization': f'Bearer {service_token}'}
    resp = client.get('/api/v1/bots', headers=auth_headers)
    assert resp.status_code == 200
    
    # 2. Test Bot existence validation on upload
    fake_bot_id = str(uuid.uuid4())
    resp = client.post(
        f'/api/v1/documents/upload?bot_id={fake_bot_id}',
        headers=auth_headers,
        files={'file': ('test.txt', b'some content', 'text/plain')}
    )
    assert resp.status_code == 404
    assert 'Bot not found' in resp.json()['detail']
    
    bot1_id = str(uuid.uuid4())
    db.execute(text('INSERT INTO bots (id, product_id, bot_name) VALUES (:id, :product_id, :bot_name)'),
               {'id': bot1_id, 'product_id': product_uuid, 'bot_name': 'Test Bot 1'})
    bot2_id = str(uuid.uuid4())
    db.execute(text('INSERT INTO bots (id, product_id, bot_name) VALUES (:id, :product_id, :bot_name)'),
               {'id': bot2_id, 'product_id': product_uuid, 'bot_name': 'Test Bot 2'})
    db.commit()
    
    # 3. Test File extension validation
    resp = client.post(
        f'/api/v1/documents/upload?bot_id={bot1_id}',
        headers=auth_headers,
        files={'file': ('exploit.exe', b'malicious binary', 'application/octet-stream')}
    )
    assert resp.status_code == 400
    assert 'Unsupported file extension' in resp.json()['detail']
    
    # 4. Test File size validation
    large_payload = b'A' * (26 * 1024 * 1024)
    resp = client.post(
        f'/api/v1/documents/upload?bot_id={bot1_id}',
        headers=auth_headers,
        files={'file': ('large.txt', large_payload, 'text/plain')}
    )
    assert resp.status_code == 400
    assert 'File exceeds the maximum limit of 25 MB' in resp.json()['detail']
    
    # 5. Test Multi-tenant duplicate hash isolation
    dummy_text = b'This is unique document content for testing multi-tenant duplicate isolation.'
    
    resp = client.post(
        f'/api/v1/documents/upload?bot_id={bot1_id}',
        headers=auth_headers,
        files={'file': ('doc.txt', dummy_text, 'text/plain')}
    )
    assert resp.status_code == 200
    job1_id = resp.json()['job_id']
    
    resp = client.post(
        f'/api/v1/documents/upload?bot_id={bot2_id}',
        headers=auth_headers,
        files={'file': ('doc.txt', dummy_text, 'text/plain')}
    )
    assert resp.status_code == 200
    job2_id = resp.json()['job_id']
    
    resp = client.post(
        f'/api/v1/documents/upload?bot_id={bot1_id}',
        headers=auth_headers,
        files={'file': ('doc.txt', dummy_text, 'text/plain')}
    )
    assert resp.status_code == 400
    assert 'Document with this hash already exists' in resp.json()['detail']
    
    # 6. Test Deterministic Point ID in Qdrant
    from src.services.qdrant_service import upsert_document_chunks
    doc_id = str(uuid.uuid4())
    chunks = [{'text': 'Chunk 1 content'}, {'text': 'Chunk 2 content'}]
    embeddings = [[0.1] * 1536, [0.2] * 1536]
    
    upsert_document_chunks(
        product_id=product_id,
        bot_id=bot1_id,
        document_id=doc_id,
        source_filename='test_det.txt',
        chunks=chunks,
        embeddings=embeddings
    )
    
    points_first, _ = qdrant_client.scroll(
        collection_name=QDRANT_COLLECTION,
        with_payload=True,
        with_vectors=False,
        limit=100
    )
    doc_points_first = [p for p in points_first if p.payload['document_id'] == doc_id]
    assert len(doc_points_first) == 2
    point_ids_first = {p.id for p in doc_points_first}
    
    upsert_document_chunks(
        product_id=product_id,
        bot_id=bot1_id,
        document_id=doc_id,
        source_filename='test_det.txt',
        chunks=chunks,
        embeddings=embeddings
    )
    
    points_second, _ = qdrant_client.scroll(
        collection_name=QDRANT_COLLECTION,
        with_payload=True,
        with_vectors=False,
        limit=100
    )
    doc_points_second = [p for p in points_second if p.payload['document_id'] == doc_id]
    assert len(doc_points_second) == 2
    point_ids_second = {p.id for p in doc_points_second}
    assert point_ids_first == point_ids_second
    
    db.execute(text('DELETE FROM document_registry WHERE bot_id IN (:b1, :b2)'), {'b1': bot1_id, 'b2': bot2_id})
    db.execute(text('DELETE FROM bots WHERE product_id = :pid'), {'pid': product_uuid})
    db.execute(text('DELETE FROM internal_products WHERE id = :pid'), {'pid': product_uuid})
    db.commit()
    
    for p_id in point_ids_first:
        qdrant_client.delete(collection_name=QDRANT_COLLECTION, points_selector=[p_id])
        
    print('=== ALL SECURITY REMEDIATION TESTS PASSED ===')

if __name__ == '__main__':
    test_security_remediation_suite()

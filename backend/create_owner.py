#!/usr/bin/env python3
"""
Script to create an owner user for the brazo tenant
Run this inside the Docker container: docker-compose exec backend python create_owner.py
"""
import sys
import os

# Add the app directory to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.core.database import SessionLocal
from app.core.security import hash_password
from app.models.tenant import Tenant
from app.models.user import User

def create_owner():
    db = SessionLocal()
    try:
        # Find or create the brazo tenant
        tenant = db.query(Tenant).filter(Tenant.slug == 'brazo').first()
        if not tenant:
            print("Creating brazo tenant...")
            tenant = Tenant(name='brazo', slug='brazo')
            db.add(tenant)
            db.flush()
            print(f"Tenant 'brazo' created with ID: {tenant.id}")
        else:
            print(f"Found tenant 'brazo' with ID: {tenant.id}")
        
        # Use default credentials
        email = 'owner@brazo.com'
        password = 'admin123'
        
        # Check if email already exists for this tenant
        existing_user = db.query(User).filter(
            User.tenant_id == tenant.id,
            User.email == email
        ).first()
        
        if existing_user:
            # Update existing user to owner role
            existing_user.role = 'owner'
            existing_user.hashed_password = hash_password(password)
            db.commit()
            db.refresh(existing_user)
            print(f"\n✓ User '{email}' updated to owner role")
            print(f"\n{'='*50}")
            print(f"CREDENTIALS:")
            print(f"{'='*50}")
            print(f"Email: {existing_user.email}")
            print(f"Password: {password}")
            print(f"Role: {existing_user.role}")
            print(f"Tenant: brazo")
            print(f"{'='*50}")
            return
        
        # Create new owner user
        owner = User(
            email=email,
            hashed_password=hash_password(password),
            role='owner',
            tenant_id=tenant.id
        )
        db.add(owner)
        db.commit()
        db.refresh(owner)
        
        print(f"\n✓ Owner user created successfully!")
        print(f"\n{'='*50}")
        print(f"CREDENTIALS:")
        print(f"{'='*50}")
        print(f"Email: {owner.email}")
        print(f"Password: {password}")
        print(f"Role: {owner.role}")
        print(f"Tenant: brazo")
        print(f"{'='*50}")
        
    except Exception as e:
        db.rollback()
        print(f"\n✗ Error creating owner user: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()

if __name__ == '__main__':
    create_owner()


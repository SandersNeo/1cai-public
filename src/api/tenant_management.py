"""
Tenant Management API
Registration, billing, usage tracking
"""

import os
import uuid
from datetime import datetime, timedelta
from typing import Dict, Any, Optional
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, EmailStr
import asyncpg
import hashlib
from src.utils.structured_logging import StructuredLogger

logger = StructuredLogger(__name__).logger

router = APIRouter(prefix="/api/tenants")


class TenantRegistrationRequest(BaseModel):
    company_name: str
    admin_email: EmailStr
    admin_name: str
    plan: str = 'starter'  # starter, professional, enterprise


class TenantManagementService:
    """Сервис управления tenants"""
    
    def __init__(self, db_pool: asyncpg.Pool):
        self.db = db_pool
        
        # Stripe (if available)
        self.stripe_available = False
        try:
            import stripe
            stripe.api_key = os.getenv("STRIPE_SECRET_KEY", "")
            if stripe.api_key:
                self.stripe = stripe
                self.stripe_available = True
        except (ImportError, Exception):
            logger.warning("Stripe not available")
    
    async def create_tenant(
        self,
        registration: TenantRegistrationRequest
    ) -> Dict[str, Any]:
        """
        Создание нового tenant
        
        Process:
        1. Create tenant record
        2. Create admin user
        3. Initialize resources (Neo4j DB, Qdrant collection, etc.)
        4. Create Stripe customer & subscription
        5. Send welcome email
        """
        
        tenant_id = uuid.uuid4()
        
        async with self.db.acquire() as conn:
            # 1. Create tenant
            await conn.execute('''
                INSERT INTO tenants (
                    id,
                    company_name,
                    plan,
                    status,
                    created_at,
                    trial_ends_at,
                    max_users,
                    max_api_calls_month,
                    max_storage_gb
                ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)
            ''',
                tenant_id,
                registration.company_name,
                registration.plan,
                'trial',
                datetime.now(),
                datetime.now() + timedelta(days=14),  # 14 days trial
                *self._get_plan_limits(registration.plan)
            )
            
            # 2. Create admin user
            admin_id = uuid.uuid4()
            temp_password = self._generate_password()
            password_hash = self._hash_password(temp_password)
            
            await conn.execute('''
                INSERT INTO users (
                    id,
                    tenant_id,
                    email,
                    name,
                    password_hash,
                    role,
                    created_at
                ) VALUES ($1, $2, $3, $4, $5, $6, $7)
            ''',
                admin_id,
                tenant_id,
                registration.admin_email,
                registration.admin_name,
                password_hash,
                'admin',
                datetime.now()
            )
        
        # 3. Initialize resources
        await self._initialize_tenant_resources(tenant_id)
        
        # 4. Create Stripe customer (if available)
        stripe_info = {}
        if self.stripe_available:
            stripe_info = await self._create_stripe_subscription(
                tenant_id,
                registration
            )
        
        # 5. Send welcome email (TODO: implement email service)
        logger.info(
            "Tenant created",
            extra={
                "tenant_id": str(tenant_id),
                "admin_email": registration.admin_email
            }
        )
        
        return {
            'tenant_id': str(tenant_id),
            'company_name': registration.company_name,
            'admin_email': registration.admin_email,
            'plan': registration.plan,
            'status': 'trial',
            'trial_ends_at': (datetime.now() + timedelta(days=14)).isoformat(),
            'temporary_password': temp_password,  # Отправим в email
            'login_url': f'https://app.1c-ai.com/login?tenant={tenant_id}',
            'stripe': stripe_info
        }
    
    def _get_plan_limits(self, plan: str) -> tuple:
        """Получение лимитов для плана"""
        
        limits = {
            'starter': (5, 10000, 5),          # users, api_calls, storage_gb
            'professional': (20, 50000, 50),
            'enterprise': (9999, 999999999, 1000)
        }
        
        return limits.get(plan, limits['starter'])
    
    async def _initialize_tenant_resources(self, tenant_id: uuid.UUID):
        """Инициализация ресурсов для tenant"""
        
        # Neo4j: create separate database
        # Qdrant: create collection
        # Elasticsearch: create index
        
        logger.info(
            "Initializing resources for tenant",
            extra={"tenant_id": str(tenant_id)}
        )
        
        # TODO: Implement actual resource initialization
        # For now - placeholder
        
        # Would create:
        # - Neo4j database: tenant_{uuid}
        # - Qdrant collection: tenant_{uuid}
        # - Elasticsearch index: tenant_{uuid}_code
    
    async def _create_stripe_subscription(
        self,
        tenant_id: uuid.UUID,
        registration: TenantRegistrationRequest
    ) -> Dict:
        """Создание Stripe customer и subscription"""
        
        try:
            # Create customer
            customer = self.stripe.Customer.create(
                email=registration.admin_email,
                name=registration.company_name,
                metadata={'tenant_id': str(tenant_id)}
            )
            
            # Get price ID for plan
            price_id = self._get_stripe_price_id(registration.plan)
            
            # Create subscription with trial
            subscription = self.stripe.Subscription.create(
                customer=customer.id,
                items=[{'price': price_id}],
                trial_period_days=14
            )
            
            # Update tenant with Stripe IDs
            async with self.db.acquire() as conn:
                await conn.execute('''
                    UPDATE tenants
                    SET stripe_customer_id = $1,
                        stripe_subscription_id = $2
                    WHERE id = $3
                ''', customer.id, subscription.id, tenant_id)
            
            return {
                'customer_id': customer.id,
                'subscription_id': subscription.id,
                'status': subscription.status
            }
            
        except Exception as e:
            logger.error(
                "Stripe error",
                extra={
                    "error": str(e),
                    "error_type": type(e).__name__
                },
                exc_info=True
            )
            return {'error': str(e)}
    
    def _get_stripe_price_id(self, plan: str) -> str:
        """Получение Stripe Price ID для плана"""
        
        # TODO: Replace with actual Stripe price IDs
        price_ids = {
            'starter': os.getenv('STRIPE_PRICE_STARTER', 'price_starter'),
            'professional': os.getenv('STRIPE_PRICE_PRO', 'price_pro'),
            'enterprise': os.getenv('STRIPE_PRICE_ENT', 'price_ent')
        }
        
        return price_ids.get(plan, price_ids['starter'])
    
    def _generate_password(self) -> str:
        """Генерация временного пароля"""
        import secrets
        import string
        
        alphabet = string.ascii_letters + string.digits
        return ''.join(secrets.choice(alphabet) for _ in range(16))
    
    def _hash_password(self, password: str) -> str:
        """Hash пароля"""
        # Simplified - в production использовать bcrypt
        return hashlib.sha256(password.encode()).hexdigest()


# FastAPI endpoints

@router.post("/register")
async def register_tenant(
    registration: TenantRegistrationRequest,
    db_pool: asyncpg.Pool = Depends(lambda: get_db_pool())
):
    """
    Регистрация нового tenant
    
    Self-serve signup:
    1. Заполнить форму
    2. Instant activation
    3. 14 days trial
    4. Credit card НЕ требуется для trial
    """
    
    service = TenantManagementService(db_pool)
    
    try:
        result = await service.create_tenant(registration)
        return result
    except Exception as e:
        logger.error(
            "Registration failed",
            extra={
                "error": str(e),
                "error_type": type(e).__name__
            },
            exc_info=True
        )
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{tenant_id}/usage")
async def get_tenant_usage(
    tenant_id: str,
    db_pool: asyncpg.Pool = Depends(lambda: get_db_pool())
):
    """Получение usage metrics для tenant"""
    
    async with db_pool.acquire() as conn:
        usage = await conn.fetchrow('''
            SELECT * FROM tenant_usage_summary
            WHERE tenant_id = $1
        ''', uuid.UUID(tenant_id))
        
        if not usage:
            raise HTTPException(status_code=404, detail="Tenant not found")
        
        return dict(usage)


def get_db_pool():
    """Dependency для получения DB pool"""
    from src.database import get_pool
    return get_pool()


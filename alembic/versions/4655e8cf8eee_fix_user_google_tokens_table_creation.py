"""Fix user_google_tokens table creation

Revision ID: 4655e8cf8eee
Revises: 64afe18b0374
Create Date: 2025-12-14 09:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy import text

# revision identifiers, used by Alembic.
revision = '4655e8cf8eee'
down_revision = '8a4d357853bb'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Создаем таблицу если её нет (безопасно)
    op.execute("""
    CREATE TABLE IF NOT EXISTS user_google_tokens (
        id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
        user_id UUID NOT NULL UNIQUE REFERENCES users(uuid) ON DELETE CASCADE,
        token_data TEXT NOT NULL,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)

    # Создаем индекс если его нет
    op.execute("""
    CREATE INDEX IF NOT EXISTS ix_user_google_tokens_user_id 
    ON user_google_tokens(user_id)
    """)


def downgrade() -> None:
    # Ничего не делаем при откате - это фиксирующая миграция
    pass
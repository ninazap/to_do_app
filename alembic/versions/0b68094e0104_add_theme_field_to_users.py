"""add_theme_field_to_users

Revision ID: 0b68094e0104
Revises: bce81662842b
Create Date: 2025-12-13 14:24:33.662590

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '0b68094e0104'
down_revision: Union[str, None] = 'bce81662842b'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Добавляем столбец theme в таблицу users
    op.add_column('users', sa.Column('theme', sa.String(length=20), server_default='light', nullable=False))

def downgrade() -> None:
    # Удаляем столбец theme
    op.drop_column('users', 'theme')

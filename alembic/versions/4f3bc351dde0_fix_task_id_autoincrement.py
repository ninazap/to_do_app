"""Fix task id autoincrement

Revision ID: 4f3bc351dde0
Revises: 539d2703e0f1
Create Date: 2025-12-15 01:59:40.383421

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '4f3bc351dde0'
down_revision: Union[str, None] = '539d2703e0f1'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Сначала создаем sequence если он не существует
    op.execute("""
    DO $$ 
    BEGIN 
        IF NOT EXISTS (SELECT 1 FROM pg_sequences WHERE sequencename = 'tasks_id_seq') THEN
            CREATE SEQUENCE tasks_id_seq START 1;
        END IF;
    END $$;
    """)

    # Затем устанавливаем его как DEFAULT для id
    op.execute("ALTER TABLE tasks ALTER COLUMN id SET DEFAULT nextval('tasks_id_seq')")

    # Также добавляем автоинкремент в метаданные SQLAlchemy
    # Это можно сделать через batch_alter_table если нужно
    op.alter_column('tasks', 'id',
                    existing_type=sa.INTEGER(),
                    server_default=sa.text("nextval('tasks_id_seq')"),
                    existing_nullable=False,
                    existing_autoincrement=True)


def downgrade() -> None:
    # Удаляем DEFAULT
    op.execute("ALTER TABLE tasks ALTER COLUMN id DROP DEFAULT")

    # Удаляем sequence (опционально)
    op.execute("DROP SEQUENCE IF EXISTS tasks_id_seq")

"""Create FAKE users data

Revision ID: fa8fcaf9ff48
Revises: 4d13e3dc4c55
Create Date: 2025-12-09 23:40:03.042686

"""
from typing import Sequence, Union

from alembic import op
import uuid
from datetime import datetime
import hashlib


# revision identifiers, used by Alembic.
revision: str = 'fa8fcaf9ff48'
down_revision: Union[str, None] = '4d13e3dc4c55'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode()).hexdigest()


def upgrade() -> None:
    # Фиксированные UUID для удобства тестирования
    users = [
        {
            'uuid': '11111111-1111-1111-1111-111111111111',
            'username': 'admin',
            'email': 'admin@example.com',
            'hashed_password': hash_password('admin123'),
            'full_name': 'Главный Администратор',
            'is_active': True,
            'is_superuser': True,
            'bio': 'Суперпользователь системы',
            'created_at': datetime.now(),
            'updated_at': datetime.now()
        },
        {
            'uuid': '22222222-2222-2222-2222-222222222222',
            'username': 'alexey',
            'email': 'alexey.ivanov@example.com',
            'hashed_password': hash_password('password123'),
            'full_name': 'Алексей Иванов',
            'is_active': True,
            'is_superuser': False,
            'bio': 'Разработчик Python',
            'created_at': datetime.now(),
            'updated_at': datetime.now()
        },
        {
            'uuid': '33333333-3333-3333-3333-333333333333',
            'username': 'maria',
            'email': 'maria.petrova@example.com',
            'hashed_password': hash_password('qwerty456'),
            'full_name': 'Мария Петрова',
            'is_active': True,
            'is_superuser': False,
            'bio': 'Project manager',
            'created_at': datetime.now(),
            'updated_at': datetime.now()
        },
        {
            'uuid': '44444444-4444-4444-4444-444444444444',
            'username': 'dmitry',
            'email': 'dmitry.sidorov@example.com',
            'hashed_password': hash_password('test789'),
            'full_name': 'Дмитрий Сидоров',
            'is_active': True,
            'is_superuser': False,
            'bio': 'QA Engineer',
            'created_at': datetime.now(),
            'updated_at': datetime.now()
        },
        {
            'uuid': '55555555-5555-5555-5555-555555555555',
            'username': 'olga',
            'email': 'olga.smirnova@example.com',
            'hashed_password': hash_password('olga2024'),
            'full_name': 'Ольга Смирнова',
            'is_active': True,
            'is_superuser': False,
            'bio': 'UI/UX дизайнер',
            'created_at': datetime.now(),
            'updated_at': datetime.now()
        }
    ]

    for user in users:
        op.execute(f"""
            INSERT INTO users (
                uuid, username, email, hashed_password, 
                full_name, is_active, is_superuser, bio, 
                created_at, updated_at
            ) VALUES (
                '{user['uuid']}',
                '{user['username']}',
                '{user['email']}',
                '{user['hashed_password']}',
                '{user['full_name']}',
                {user['is_active']},
                {user['is_superuser']},
                '{user['bio']}',
                '{user['created_at']}',
                '{user['updated_at']}'
            )
        """)


def downgrade() -> None:
    op.execute("""
        DELETE FROM users 
        WHERE uuid IN (
            '11111111-1111-1111-1111-111111111111',
            '22222222-2222-2222-2222-222222222222',
            '33333333-3333-3333-3333-333333333333',
            '44444444-4444-4444-4444-444444444444',
            '55555555-5555-5555-5555-555555555555'
        )
    """)


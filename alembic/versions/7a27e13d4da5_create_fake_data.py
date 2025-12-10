"""Create FAKE data

Revision ID: 7a27e13d4da5
Revises: 3c83a6a43d3e
Create Date: 2025-12-09 23:18:01.267042

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
import uuid
from datetime import datetime

# revision identifiers, used by Alembic.
revision: str = '7a27e13d4da5'
down_revision: Union[str, None] = '3c83a6a43d3e'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    categories = [
        {
            'uuid': str(uuid.uuid4()),
            'name': 'Работа',
            'desc': 'Рабочие задачи и проекты',
            'create_at': datetime.now(),
            'update_at': datetime.now()
        },
        {
            'uuid': str(uuid.uuid4()),
            'name': 'Личное',
            'desc': 'Личные дела и хобби',
            'create_at': datetime.now(),
            'update_at': datetime.now()
        },
        {
            'uuid': str(uuid.uuid4()),
            'name': 'Здоровье',
            'desc': 'Спорт и медицинские вопросы',
            'create_at': datetime.now(),
            'update_at': datetime.now()
        },
        {
            'uuid': str(uuid.uuid4()),
            'name': 'Обучение',
            'desc': 'Курсы, книги и саморазвитие',
            'create_at': datetime.now(),
            'update_at': datetime.now()
        },
        {
            'uuid': str(uuid.uuid4()),
            'name': 'Финансы',
            'desc': 'Бюджет, счета и инвестиции',
            'create_at': datetime.now(),
            'update_at': datetime.now()
        }
    ]

    for category in categories:
        op.execute(f"""
            INSERT INTO category (uuid, name, "desc", create_at, update_at)
            VALUES (
                '{category['uuid']}',
                '{category['name']}',
                '{category['desc'].replace("'", "''")}',
                '{category['create_at']}',
                '{category['update_at']}'
            )
        """)

    work_category = categories[0]['uuid']
    personal_category = categories[1]['uuid']
    health_category = categories[2]['uuid']
    learning_category = categories[3]['uuid']
    finance_category = categories[4]['uuid']

    tasks = [
        (str(uuid.uuid4()), 'Подготовить отчет за квартал', work_category),
        (str(uuid.uuid4()), 'Провести собрание команды', work_category),
        (str(uuid.uuid4()), 'Ответить на письма', work_category),
        (str(uuid.uuid4()), 'Сходить в магазин за продуктами', personal_category),
        (str(uuid.uuid4()), 'Позвонить родителям', personal_category),
        (str(uuid.uuid4()), 'Записаться к врачу на осмотр', health_category),
        (str(uuid.uuid4()), 'Сходить на тренировку', health_category),
        (str(uuid.uuid4()), 'Прочитать новую книгу по программированию', learning_category),
        (str(uuid.uuid4()), 'Пройди онлайн-курс по базам данных', learning_category),
        (str(uuid.uuid4()), 'Оплатить счета за коммунальные услуги', finance_category),
        (str(uuid.uuid4()), 'Составить бюджет на следующий месяц', finance_category),
        (str(uuid.uuid4()), 'Задача без категории', None),
    ]

    for task_uuid, task_desc, category_id in tasks:
        category_sql = f"'{category_id}'" if category_id else 'NULL'
        op.execute(f"""
            INSERT INTO tasks (uuid, task_id, "desc", category_id, create_at, update_at)
            VALUES (
                '{task_uuid}',
                '{task_uuid}',
                '{task_desc.replace("'", "''")}',
                {category_sql},
                '{datetime.now()}',
                '{datetime.now()}'
            )
        """)


def downgrade() -> None:
    op.execute("DELETE FROM tasks")
    op.execute("DELETE FROM category")


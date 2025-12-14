import json
import os
import logging
from datetime import datetime
from typing import Optional, Dict, Any, Tuple, List
from urllib.parse import urlencode

from sqlalchemy.orm import Session
import uuid
import httplib2

from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import Flow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

from app.core.config import settings
from app.models.user_google_token import UserGoogleToken
from app.crud.google_token import get_google_token

logger = logging.getLogger(__name__)

# Scopes для Google Tasks API
SCOPES = ['https://www.googleapis.com/auth/tasks']


class GoogleTasksService:
    def __init__(self):
        self.client_id = settings.GOOGLE_CLIENT_ID
        self.client_secret = settings.GOOGLE_CLIENT_SECRET
        self.redirect_uri = settings.GOOGLE_REDIRECT_URI

        logger.info(f"Google Tasks Service initialized with client_id: {self.client_id[:10]}...")
        logger.info(f"Redirect URI: {self.redirect_uri}")

        if not self.client_id or not self.client_secret:
            logger.warning("Google OAuth credentials not configured properly")

        # Инициализируем OAuth flow
        self._setup_oauth_flow()

    def _setup_oauth_flow(self):
        """Настраивает OAuth flow с использованием credentials.json"""
        try:
            # Используем credentials.json если он существует
            if os.path.exists('credentials.json'):
                logger.info("Using credentials.json for OAuth flow")
                self.flow = Flow.from_client_secrets_file(
                    'credentials.json',
                    scopes=SCOPES,
                    redirect_uri=self.redirect_uri
                )
            else:
                # Используем переменные окружения
                logger.info("Using environment variables for OAuth flow")
                client_config = {
                    "web": {
                        "client_id": self.client_id,
                        "client_secret": self.client_secret,
                        "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                        "token_uri": "https://oauth2.googleapis.com/token",
                        "redirect_uris": [self.redirect_uri],
                        "token_uri": "https://oauth2.googleapis.com/token"
                    }
                }
                self.flow = Flow.from_client_config(
                    client_config,
                    scopes=SCOPES,
                    redirect_uri=self.redirect_uri
                )

            logger.info("OAuth flow setup completed successfully")
        except Exception as e:
            logger.error(f"Error setting up OAuth flow: {e}")
            self.flow = None

    def get_authorization_url(self, user_id: str) -> Tuple[str, str]:
        """Получить URL для авторизации пользователя в Google"""
        try:
            if not self.flow:
                raise ValueError("OAuth flow not initialized. Check Google credentials.")

            # Генерируем state для безопасности
            state = json.dumps({"user_id": str(user_id), "timestamp": datetime.utcnow().isoformat()})

            # Генерируем URL для авторизации
            auth_url, _ = self.flow.authorization_url(
                access_type='offline',
                include_granted_scopes='true',
                state=state,
                prompt='consent'
            )

            logger.info(f"Generated auth URL for user {user_id}")
            return auth_url, state

        except Exception as e:
            logger.error(f"Error generating auth URL: {e}")
            raise HTTPException(status_code=500, detail=f"Failed to generate auth URL: {str(e)}")

    def exchange_code_for_tokens(self, code: str) -> Optional[Dict[str, Any]]:
        """Обменять authorization code на токены"""
        try:
            if not self.flow:
                raise ValueError("OAuth flow not initialized")

            # Получаем токены от Google
            self.flow.fetch_token(code=code)
            credentials = self.flow.credentials

            # Конвертируем в словарь
            token_data = {
                'token': credentials.token,
                'refresh_token': credentials.refresh_token,
                'token_uri': credentials.token_uri,
                'client_id': credentials.client_id,
                'client_secret': credentials.client_secret,
                'scopes': credentials.scopes,
                'expiry': credentials.expiry.isoformat() if credentials.expiry else None
            }

            logger.info("Successfully exchanged code for tokens")
            return token_data

        except Exception as e:
            logger.error(f"Error exchanging code for tokens: {e}")
            return None

    def save_credentials_from_code(self, db: Session, code: str, user_id: str) -> bool:
        """Сохранить токены в базу данных"""
        try:
            # Получаем токены от Google
            token_data = self.exchange_code_for_tokens(code)
            if not token_data:
                return False

            # Сохраняем в базу
            return self._save_token_data(db, user_id, token_data)

        except Exception as e:
            logger.error(f"Error saving credentials: {e}")
            return False

    def _save_token_data(self, db: Session, user_id: str, token_data: Dict[str, Any]) -> bool:
        """Сохранить токен в базу данных"""
        try:
            user_uuid = uuid.UUID(user_id)

            # Проверяем существующий токен
            existing_token = get_google_token(db, user_id)

            if existing_token:
                # Обновляем
                existing_token.token_data = json.dumps(token_data)
                existing_token.updated_at = datetime.utcnow()
            else:
                # Создаем новый
                new_token = UserGoogleToken(
                    user_id=user_uuid,
                    token_data=json.dumps(token_data)
                )
                db.add(new_token)

            db.commit()
            logger.info(f"Token saved for user {user_id}")
            return True

        except Exception as e:
            logger.error(f"Error saving token to database: {e}")
            db.rollback()
            return False

    def get_credentials(self, db: Session, user_id: str) -> Optional[Credentials]:
        """Получить credentials для пользователя - РАСШИРЕННАЯ ДИАГНОСТИКА"""
        print(f"\n=== [GOOGLE DEBUG] get_credentials для user_id: {user_id} ===")

        try:
            # 1. Получаем токен из БД
            token_record = get_google_token(db, user_id)
            if not token_record:
                print(f"[GOOGLE DEBUG] ❌ Токен не найден в БД")
                return None
            print(f"[GOOGLE DEBUG] ✅ Запись токена найдена. ID: {token_record.id}")

            # 2. Пытаемся распарсить JSON
            try:
                token_data = json.loads(token_record.token_data)
                print(f"[GOOGLE DEBUG] ✅ JSON успешно распарсен")
            except json.JSONDecodeError as e:
                print(f"[GOOGLE DEBUG] ❌ Ошибка парсинга JSON: {e}")
                print(f"[GOOGLE DEBUG] Сырые данные (первые 500 символов): {token_record.token_data[:500]}")
                return None

            # 3. Проверяем структуру токена (КРИТИЧЕСКИ ВАЖНЫЙ ШАГ)
            print(f"[GOOGLE DEBUG] Проверяем структуру токена...")
            print(f"[GOOGLE DEBUG] Ключи в token_data: {list(token_data.keys())}")

            # Проверяем наличие ВСЕХ необходимых полей
            required_fields = ['token', 'refresh_token', 'client_id', 'client_secret', 'scopes']
            for field in required_fields:
                if field not in token_data:
                    print(f"[GOOGLE DEBUG] ❌ Отсутствует обязательное поле: {field}")
                else:
                    value_preview = str(token_data[field])[:50] + "..." if len(str(token_data[field])) > 50 else str(
                        token_data[field])
                    print(f"[GOOGLE DEBUG]   {field}: {value_preview}")

            # 4. Проверяем, не истек ли токен
            if 'expiry' in token_data:
                expiry_time = datetime.fromisoformat(token_data['expiry'].replace('Z', '+00:00'))
                now = datetime.utcnow()
                print(f"[GOOGLE DEBUG] Срок действия истекает: {expiry_time}")
                print(f"[GOOGLE DEBUG] Текущее время UTC: {now}")
                print(f"[GOOGLE DEBUG] Токен истек: {expiry_time < now}")
            else:
                print(f"[GOOGLE DEBUG] Внимание: поле 'expiry' отсутствует в token_data")

            # 5. Пытаемся создать объект Credentials
            print(f"[GOOGLE DEBUG] Создаем объект google.oauth2.credentials.Credentials...")
            try:
                # Важно: передаем ВСЕ параметры как есть из token_data
                credentials = Credentials(
                    token=token_data.get('token'),
                    refresh_token=token_data.get('refresh_token'),
                    token_uri=token_data.get('token_uri', 'https://oauth2.googleapis.com/token'),
                    client_id=token_data.get('client_id'),
                    client_secret=token_data.get('client_secret'),
                    scopes=token_data.get('scopes'),
                    expiry=datetime.fromisoformat(
                        token_data['expiry'].replace('Z', '+00:00')) if 'expiry' in token_data else None
                )

                print(f"[GOOGLE DEBUG] ✅ Объект Credentials успешно создан")
                print(f"[GOOGLE DEBUG] Тип credentials: {type(credentials)}")
                print(
                    f"[GOOGLE DEBUG] Методы объекта: {[m for m in dir(credentials) if not m.startswith('_')][:10]}...")

                return credentials

            except Exception as e:
                print(f"[GOOGLE DEBUG] ❌ Ошибка при создании Credentials: {e}")
                import traceback
                print(f"[GOOGLE DEBUG] Traceback:\n{traceback.format_exc()}")
                return None

        except Exception as e:
            print(f"[GOOGLE DEBUG] ❌ Неожиданная ошибка в get_credentials: {e}")
            import traceback
            print(f"[GOOGLE DEBUG] Traceback:\n{traceback.format_exc()}")
            return None

    def get_tasks_service(self, db: Session, user_id: str):
        """Получить сервис Google Tasks для пользователя - ИСПРАВЛЕННАЯ ВЕРСИЯ"""
        print(f"\n=== [GOOGLE DEBUG] Создание Tasks service для user_id: {user_id} ===")

        try:
            credentials = self.get_credentials(db, user_id)
            if not credentials:
                print("[GOOGLE DEBUG] ❌ Не удалось получить credentials")
                return None

            print("[GOOGLE DEBUG] ✅ Credentials получены")
            print(f"[GOOGLE DEBUG] Токен истек: {credentials.expired}")

            # СПОСОБ 1: Прямая передача credentials в build() (рекомендуется)
            try:
                print("[GOOGLE DEBUG] Пробуем создать service с прямым использованием credentials...")
                service = build('tasks', 'v1', credentials=credentials, static_discovery=False)
                print("[GOOGLE DEBUG] ✅ Service создан успешно (способ 1)")
                return service
            except Exception as e1:
                print(f"[GOOGLE DEBUG] Способ 1 не сработал: {e1}")

                # СПОСОБ 2: Через создание авторизованного HTTP-клиента
                try:
                    print("[GOOGLE DEBUG] Пробуем создать service через авторизованный HTTP...")
                    import google.auth.transport.requests
                    from google.oauth2.credentials import Credentials

                    # Обновляем токен, если истек
                    if credentials.expired and credentials.refresh_token:
                        print("[GOOGLE DEBUG] Обновляем истекший токен...")
                        request = google.auth.transport.requests.Request()
                        credentials.refresh(request)

                    # Создаем авторизованный HTTP-клиент
                    authed_http = google.auth.transport.requests.AuthorizedSession(credentials)

                    # Создаем сервис
                    service = build('tasks', 'v1', http=authed_http, static_discovery=False)
                    print("[GOOGLE DEBUG] ✅ Service создан успешно (способ 2)")
                    return service

                except Exception as e2:
                    print(f"[GOOGLE DEBUG] Способ 2 не сработал: {e2}")
                    return None

        except Exception as e:
            print(f"[GOOGLE DEBUG] ❌ Общая ошибка создания service: {e}")
            import traceback
            print(f"[GOOGLE DEBUG] Traceback:\n{traceback.format_exc()}")
            return None

    def create_google_task(self, db: Session, user_id: str, task_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Создать задачу в Google Tasks с улучшенной обработкой ошибок"""
        try:
            service = self.get_tasks_service(db, user_id)
            if not service:
                logger.error(f"Cannot create task: no service for user {user_id}")
                return None

            # Подготавливаем задачу для Google Tasks API
            google_task = {
                'title': task_data.get('title', 'Untitled Task')[:1024],  # Ограничиваем длину
                'notes': task_data.get('description') or task_data.get('notes') or '',
                'status': 'needsAction'
            }

            # Добавляем due date если есть
            if task_data.get('due_date'):
                due_date = task_data['due_date']
                try:
                    if isinstance(due_date, datetime):
                        google_task['due'] = due_date.isoformat() + 'Z'
                    elif isinstance(due_date, str):
                        # Пробуем парсить строку
                        parsed_date = datetime.fromisoformat(due_date.replace('Z', '+00:00'))
                        google_task['due'] = parsed_date.isoformat() + 'Z'
                except Exception as e:
                    logger.warning(f"Could not parse due date '{due_date}': {e}")
                    # Продолжаем без due date

            # Используем default tasklist
            tasklist_id = '@default'

            # Создаем задачу
            logger.info(f"Creating Google Task: '{google_task['title']}'")

            try:
                result = service.tasks().insert(
                    tasklist=tasklist_id,
                    body=google_task
                ).execute()

                logger.info(f"Google Task created successfully: {result.get('id')}")
                return result

            except HttpError as e:
                logger.error(f"Google API HTTP error creating task: {e}")
                return None
            except Exception as e:
                logger.error(f"Google API error creating task: {e}")
                return None

        except Exception as e:
            logger.error(f"Error in create_google_task: {e}")
            return None

    def export_user_tasks(self, db: Session, user_id: str, tasks: list) -> Dict[str, Any]:
        """Экспортировать задачи пользователя в Google Tasks"""
        logger.info(f"Starting export of {len(tasks)} tasks for user {user_id}")

        # ДИАГНОСТИКА 1: Проверяем наличие токена в БД
        try:
            from app.crud.google_token import get_google_token
            token_record = get_google_token(db, user_id)

            if not token_record:
                logger.error(f"No Google token found in DB for user {user_id}")
                return {
                    'total': len(tasks),
                    'success': 0,
                    'failed': len(tasks),
                    'error': 'Google authentication required. Please connect your Google account first.',
                    'exported_tasks': [],
                    'failed_tasks': []
                }

            logger.info(f"Token found in DB for user {user_id}")
        except Exception as e:
            logger.error(f"Error checking token in DB: {e}")
            return {
                'total': len(tasks),
                'success': 0,
                'failed': len(tasks),
                'error': f'Database error: {str(e)}',
                'exported_tasks': [],
                'failed_tasks': []
            }

        # ДИАГНОСТИКА 2: Получаем сервис
        try:
            service = self.get_tasks_service(db, user_id)
            if not service:
                logger.error(f"Failed to get Google Tasks service for user {user_id}")
                return {
                    'total': len(tasks),
                    'success': 0,
                    'failed': len(tasks),
                    'error': 'Failed to authenticate with Google. Token may be invalid.',
                    'exported_tasks': [],
                    'failed_tasks': []
                }

            logger.info(f"Google Tasks service created successfully for user {user_id}")
        except Exception as e:
            logger.error(f"Error creating Google Tasks service: {e}")
            return {
                'total': len(tasks),
                'success': 0,
                'failed': len(tasks),
                'error': f'Google API error: {str(e)}',
                'exported_tasks': [],
                'failed_tasks': []
            }

        # Экспорт задач
        exported_tasks = []
        failed_tasks = []

        for task in tasks:
            try:
                # Подготавливаем данные задачи для Google
                task_data = {
                    'title': getattr(task, 'title', 'Untitled Task'),
                    'description': getattr(task, 'description', ''),
                }

                # Добавляем due date если есть
                if hasattr(task, 'due_date') and task.due_date:
                    task_data['due_date'] = task.due_date

                # Создаем задачу в Google Tasks
                google_task = self.create_google_task(db, user_id, task_data)

                if google_task:
                    # Сохраняем Google Task ID в нашу БД
                    try:
                        # Проверяем, что модель Task имеет нужные поля
                        if hasattr(task, 'google_task_id'):
                            task.google_task_id = google_task.get('id')
                            task.synced_with_google_at = datetime.utcnow()

                            # Сохраняем tasklist_id если поле есть
                            if hasattr(task, 'google_tasklist_id'):
                                task.google_tasklist_id = '@default'

                            # Коммитим изменения
                            db.add(task)
                            db.commit()

                            logger.info(
                                f"Saved google_task_id '{google_task.get('id')}' for task {getattr(task, 'id', 'unknown')}")
                        else:
                            logger.warning(f"Task model doesn't have google_task_id field. Model fields: {dir(task)}")
                    except Exception as e:
                        logger.warning(f"Could not save google_task_id to DB (continuing anyway): {e}")
                        db.rollback()  # Откатываем изменения если ошибка

                    # Добавляем в результат
                    exported_tasks.append({
                        'task_id': getattr(task, 'id', None),
                        'google_task_id': google_task.get('id'),
                        'title': google_task.get('title'),
                        'link': f"https://tasks.google.com/task/{google_task.get('id')}"
                    })

                    logger.info(f"Successfully exported task '{google_task.get('title')}' to Google Tasks")
                else:
                    # Не удалось создать задачу в Google
                    failed_tasks.append({
                        'task_id': getattr(task, 'id', None),
                        'error': 'Failed to create task in Google Tasks',
                        'title': getattr(task, 'title', 'Unknown')
                    })
                    logger.warning(f"Failed to export task {getattr(task, 'id', 'unknown')}")

            except Exception as e:
                logger.error(f"Error exporting task {getattr(task, 'id', 'unknown')}: {e}")
                failed_tasks.append({
                    'task_id': getattr(task, 'id', None),
                    'error': str(e),
                    'title': getattr(task, 'title', 'Unknown')[:50]
                })

        # Формируем итоговый результат
        result = {
            'total': len(tasks),
            'success': len(exported_tasks),
            'failed': len(failed_tasks),
            'error': None if len(failed_tasks) == 0 else f'{len(failed_tasks)} of {len(tasks)} tasks failed',
            'exported_tasks': exported_tasks,
            'failed_tasks': failed_tasks
        }

        if len(failed_tasks) == 0:
            logger.info(f"Export completed successfully: {result['success']} tasks exported")
        else:
            logger.warning(f"Export completed with errors: {result['success']} successful, {result['failed']} failed")

        return result

    def test_connection(self, db: Session, user_id: str) -> Dict[str, Any]:
        """Проверить подключение к Google Tasks"""
        try:
            service = self.get_tasks_service(db, user_id)
            if not service:
                return {"connected": False, "message": "No valid credentials"}

            # Пробуем получить tasklists
            tasklists = service.tasklists().list().execute()

            return {
                "connected": True,
                "message": "Successfully connected to Google Tasks",
                "tasklists_count": len(tasklists.get('items', [])),
                "email": self.get_user_email(service)
            }

        except HttpError as e:
            logger.error(f"Google API error in test_connection: {e}")
            return {"connected": False, "message": f"Google API error: {str(e)}"}
        except Exception as e:
            logger.error(f"Error in test_connection: {e}")
            return {"connected": False, "message": str(e)}

    def get_user_email(self, service) -> Optional[str]:
        """Получить email пользователя"""
        try:
            # Используем Google People API для получения email
            people_service = build('people', 'v1', credentials=service._http.credentials, static_discovery=False)
            profile = people_service.people().get(
                resourceName='people/me',
                personFields='emailAddresses'
            ).execute()

            emails = profile.get('emailAddresses', [])
            if emails:
                return emails[0].get('value')
        except Exception:
            # Если не удалось, возвращаем None
            pass
        return None

    def sync_tasks_from_google(self, db: Session, user_id: str, tasklist_id: str = '@default') -> Dict[str, Any]:
        """Полная синхронизация задач между Google Tasks и локальной БД"""
        try:
            logger.info(f"=== STARTING FULL SYNC for user {user_id} ===")

            # 1. Проверяем подключение
            service = self.get_tasks_service(db, user_id)
            if not service:
                logger.error(f"No Google service for user {user_id}")
                return {
                    "status": "error",
                    "message": "Google authentication required",
                    "details": {
                        "synced": 0,
                        "created": 0,
                        "updated": 0,
                        "deleted": 0,
                        "failed": 0,
                        "total_google_tasks": 0,
                        "total_local_tasks": 0
                    }
                }

            # 2. Получаем задачи из Google
            logger.info("Fetching tasks from Google Tasks...")
            try:
                google_tasks_result = service.tasks().list(
                    tasklist=tasklist_id,
                    showCompleted=True,
                    showHidden=False,
                    maxResults=1000  # Большой лимит для полной синхронизации
                ).execute()
                google_tasks = google_tasks_result.get('items', [])
                logger.info(f"Retrieved {len(google_tasks)} tasks from Google")
            except Exception as e:
                logger.error(f"Error fetching Google tasks: {e}")
                return {
                    "status": "error",
                    "message": f"Failed to fetch Google tasks: {str(e)}",
                    "details": {"synced": 0, "created": 0, "updated": 0, "deleted": 0, "failed": 0}
                }

            # 3. Фильтруем задачи Google перед обработкой
            filtered_google_tasks = []
            processed_google_ids = set()

            for google_task in google_tasks:
                google_task_id = google_task.get('id')
                google_title = google_task.get('title', '').strip()

                # Пропускаем задачи без ID
                if not google_task_id:
                    logger.warning(f"Skipping task without ID: '{google_title}'")
                    continue

                # Пропускаем задачи с пустым заголовком
                if not google_title:
                    logger.warning(f"Skipping task with empty title: {google_task_id}")
                    continue

                # Пропускаем уже обработанные задачи (на случай дубликатов в ответе API)
                if google_task_id in processed_google_ids:
                    logger.warning(f"Skipping duplicate google_task_id in API response: {google_task_id}")
                    continue

                processed_google_ids.add(google_task_id)
                filtered_google_tasks.append(google_task)

            google_tasks = filtered_google_tasks
            logger.info(f"After filtering: {len(google_tasks)} valid tasks from Google")

            # 4. Получаем задачи пользователя из локальной БД
            from app.crud.task import get_tasks_by_user
            local_tasks = get_tasks_by_user(db, user_id)

            # Создаем индексы для быстрого поиска
            local_tasks_by_id = {task.id: task for task in local_tasks}
            local_tasks_by_google_id = {
                task.google_task_id: task
                for task in local_tasks
                if task.google_task_id
            }

            # Дополнительный индекс для поиска дубликатов по содержимому
            local_tasks_by_content = {}
            for task in local_tasks:
                if task.title:
                    title_key = task.title.strip().lower()
                    desc_key = (task.description or "").strip().lower()
                    content_key = f"{title_key}|{desc_key}"
                    local_tasks_by_content[content_key] = task

            # 5. Синхронизация
            stats = {
                "created": 0,
                "updated": 0,
                "deleted": 0,
                "failed": 0,
                "duplicates_merged": 0,
                "total_google_tasks": len(google_tasks),
                "total_local_tasks_before": len(local_tasks)
            }

            # А. Обновляем/создаем задачи на основе Google
            logger.info("Syncing from Google to local DB...")

            # Отслеживаем созданные задачи в этой сессии синхронизации
            newly_created_tasks_by_google_id = {}
            newly_created_tasks_by_content = {}

            for google_task in google_tasks:
                try:
                    google_task_id = google_task.get('id')
                    google_title = google_task.get('title', '').strip()
                    google_notes = google_task.get('notes', '').strip()

                    # Формируем ключ содержимого для поиска дубликатов
                    content_key = f"{google_title.lower()}|{google_notes.lower()}"

                    # 1. Проверяем по google_task_id в существующих задачах
                    local_task = local_tasks_by_google_id.get(google_task_id)

                    # 2. Проверяем по google_task_id в только что созданных задачах
                    if not local_task:
                        local_task = newly_created_tasks_by_google_id.get(google_task_id)

                    # 3. Если задача не найдена по google_id, ищем по содержимому
                    if not local_task:
                        local_task = local_tasks_by_content.get(content_key)

                        # Если нашли по содержимому (но с другим google_id)
                        if local_task and local_task.google_task_id != google_task_id:
                            logger.info(
                                f"Merging duplicate by content: task {local_task.id}, updating google_id from {local_task.google_task_id} to {google_task_id}")
                            local_task.google_task_id = google_task_id
                            local_task.synced_with_google_at = datetime.utcnow()
                            stats["duplicates_merged"] += 1

                    # 4. Проверяем в только что созданных задачах по содержимому
                    if not local_task:
                        local_task = newly_created_tasks_by_content.get(content_key)

                    if local_task:
                        # Обновляем существующую задачу
                        changed = self._update_local_task_from_google(local_task, google_task)
                        if changed:
                            stats["updated"] += 1
                            logger.info(f"Updated task: {local_task.id} - '{google_title}'")
                    else:
                        # Создаем новую задачу
                        local_task = self._create_local_task_from_google(
                            db, user_id, google_task, tasklist_id
                        )
                        if local_task:
                            stats["created"] += 1
                            logger.info(f"Created task: {local_task.id} - '{google_title}'")

                            # Добавляем в индексы созданных задач
                            newly_created_tasks_by_google_id[google_task_id] = local_task
                            newly_created_tasks_by_content[content_key] = local_task
                        else:
                            stats["failed"] += 1

                except Exception as e:
                    stats["failed"] += 1
                    logger.error(f"Error syncing Google task {google_task.get('id')}: {e}")

            # Б. Помечаем на удаление локальные задачи, которых нет в Google
            logger.info("Checking for tasks to delete...")
            google_ids = {task.get('id') for task in google_tasks}

            # Добавляем google_id из только что созданных задач
            for google_id in newly_created_tasks_by_google_id:
                google_ids.add(google_id)

            for local_task in local_tasks:
                # Удаляем только задачи, которые были синхронизированы с Google
                if local_task.google_task_id and local_task.google_task_id not in google_ids:
                    try:
                        # Удаляем задачу из локальной БД
                        db.delete(local_task)
                        stats["deleted"] += 1
                        logger.info(f"Marked for deletion: {local_task.id} - '{local_task.title}'")
                    except Exception as e:
                        stats["failed"] += 1
                        logger.error(f"Error deleting task {local_task.id}: {e}")

            # Коммитим изменения
            db.commit()

            # 6. Получаем итоговое количество задач
            local_tasks_after = get_tasks_by_user(db, user_id)
            stats["total_local_tasks_after"] = len(local_tasks_after)

            logger.info(f"=== SYNC COMPLETED: "
                        f"Created: {stats['created']}, "
                        f"Updated: {stats['updated']}, "
                        f"Deleted: {stats['deleted']}, "
                        f"Merged: {stats['duplicates_merged']}, "
                        f"Failed: {stats['failed']} ===")

            return {
                "status": "success",
                "message": "Sync completed successfully",
                "details": stats
            }

        except Exception as e:
            logger.error(f"Error in sync_tasks_from_google: {e}")
            db.rollback()
            return {
                "status": "error",
                "message": f"Sync failed: {str(e)}",
                "details": {"synced": 0, "created": 0, "updated": 0, "deleted": 0, "failed": 0}
            }

    def _update_local_task_from_google(self, local_task, google_task: Dict[str, Any]) -> bool:
        """Обновить локальную задачу на основе данных из Google Tasks"""
        changed = False

        # Обновляем заголовок
        google_title = google_task.get('title', '')
        if google_title and local_task.title != google_title:
            local_task.title = google_title
            changed = True

        # Обновляем описание
        google_notes = google_task.get('notes', '')
        if google_notes is not None and local_task.description != google_notes:
            local_task.description = google_notes
            changed = True

        # Обновляем статус выполнения
        google_status = google_task.get('status')
        is_completed_in_google = google_status == 'completed'

        if local_task.is_completed != is_completed_in_google:
            local_task.is_completed = is_completed_in_google
            changed = True

        # Обновляем due date если есть
        if 'due' in google_task:
            try:
                due_date = datetime.fromisoformat(google_task['due'].replace('Z', '+00:00'))
                # Если у local_task есть поле due_date, обновляем его
                if hasattr(local_task, 'due_date') and local_task.due_date != due_date:
                    local_task.due_date = due_date
                    changed = True
            except Exception as e:
                logger.warning(f"Could not parse due date: {e}")

        if changed:
            local_task.synced_with_google_at = datetime.utcnow()

        return changed

    def _create_local_task_from_google(self, db: Session, user_id: str,
                                       google_task: Dict[str, Any], tasklist_id: str):
        """Создать локальную задачу на основе задачи из Google"""
        try:
            # Получаем и очищаем данные из Google
            google_task_id = google_task.get('id')
            google_title = google_task.get('title', '').strip()
            google_notes = google_task.get('notes', '').strip()

            # ВАЛИДАЦИЯ: Пропускаем задачи без ID или с пустым заголовком
            if not google_task_id:
                logger.warning("Cannot create task: missing google_task_id")
                return None

            if not google_title:
                logger.warning(f"Skipping task creation: empty title for google_id {google_task_id}")
                return None

            # ДОПОЛНИТЕЛЬНАЯ ПРОВЕРКА: убедимся, что задачи с таким google_task_id ещё нет в БД
            from app.models.task import Task

            # Проверяем по google_task_id
            existing_by_google_id = db.query(Task).filter(
                Task.user_id == uuid.UUID(user_id),
                Task.google_task_id == google_task_id
            ).first()

            if existing_by_google_id:
                logger.info(f"Task already exists with google_id {google_task_id} (ID: {existing_by_google_id.id})")
                return existing_by_google_id

            # Если дошли сюда, создаем новую задачу
            new_task = Task(
                user_id=uuid.UUID(user_id),
                title=google_title,
                description=google_notes,
                is_completed=google_task.get('status') == 'completed',
                google_task_id=google_task_id,
                google_tasklist_id=tasklist_id,
                synced_with_google_at=datetime.utcnow()
            )

            # Добавляем due date если есть
            if 'due' in google_task:
                try:
                    due_date = datetime.fromisoformat(google_task['due'].replace('Z', '+00:00'))
                    if hasattr(new_task, 'due_date'):
                        new_task.due_date = due_date
                except Exception as e:
                    logger.warning(f"Could not parse due date for task {google_task_id}: {e}")

            # Сохраняем в БД
            db.add(new_task)
            db.flush()  # Получаем ID

            logger.debug(f"Created new task from Google: ID={new_task.id}, google_id={google_task_id}")
            return new_task

        except Exception as e:
            logger.error(f"Error creating local task from Google: {e}")
            import traceback
            logger.error(f"Traceback: {traceback.format_exc()}")
            return None

    def cleanup_duplicate_tasks(self, db: Session, user_id: str) -> Dict[str, Any]:
        """Очистка существующих дубликатов задач в базе данных"""
        try:
            from app.models.task import Task
            from sqlalchemy import and_

            logger.info(f"=== STARTING DUPLICATE CLEANUP for user {user_id} ===")

            # Получаем все задачи пользователя
            user_tasks = db.query(Task).filter(
                Task.user_id == uuid.UUID(user_id)
            ).all()

            logger.info(f"Found {len(user_tasks)} total tasks for user")

            # Создаем структуры для поиска дубликатов
            tasks_by_google_id = {}
            tasks_by_content = {}
            duplicate_groups = []

            # Группируем задачи по google_task_id
            for task in user_tasks:
                if task.google_task_id:
                    if task.google_task_id in tasks_by_google_id:
                        tasks_by_google_id[task.google_task_id].append(task)
                    else:
                        tasks_by_google_id[task.google_task_id] = [task]

            # Находим дубликаты по google_task_id
            duplicate_stats = {
                "total_tasks": len(user_tasks),
                "duplicates_by_google_id": 0,
                "duplicates_by_content": 0,
                "kept": 0,
                "deleted": 0,
                "merged": 0
            }

            # Обрабатываем дубликаты по google_task_id
            for google_id, tasks in tasks_by_google_id.items():
                if len(tasks) > 1:
                    logger.info(f"Found {len(tasks)} duplicates for google_id: {google_id}")
                    duplicate_stats["duplicates_by_google_id"] += len(tasks) - 1

                    # Сортируем задачи: сначала задачи с более поздней синхронизацией
                    tasks.sort(key=lambda x: x.synced_with_google_at or datetime.min, reverse=True)

                    # Оставляем первую задачу (самую свежую), остальные удаляем
                    task_to_keep = tasks[0]
                    for task_to_delete in tasks[1:]:
                        logger.info(f"Deleting duplicate task {task_to_delete.id} (keeping {task_to_keep.id})")
                        db.delete(task_to_delete)
                        duplicate_stats["deleted"] += 1

                    duplicate_stats["kept"] += 1

            # Теперь ищем дубликаты по содержимому среди оставшихся задач
            # Получаем обновленный список задач
            remaining_tasks = db.query(Task).filter(
                Task.user_id == uuid.UUID(user_id)
            ).all()

            # Группируем по содержимому (заголовок + описание)
            tasks_by_content = {}
            for task in remaining_tasks:
                if task.title:
                    title_key = (task.title or "").strip().lower()
                    desc_key = (task.description or "").strip().lower()
                    content_key = f"{title_key}|{desc_key}"

                    if content_key not in tasks_by_content:
                        tasks_by_content[content_key] = []
                    tasks_by_content[content_key].append(task)

            # Обрабатываем дубликаты по содержимому
            for content_key, tasks in tasks_by_content.items():
                if len(tasks) > 1:
                    logger.info(f"Found {len(tasks)} duplicates by content: '{tasks[0].title}'")
                    duplicate_stats["duplicates_by_content"] += len(tasks) - 1

                    # Ищем задачу с google_task_id (она имеет приоритет)
                    tasks_with_google = [t for t in tasks if t.google_task_id]
                    tasks_without_google = [t for t in tasks if not t.google_task_id]

                    if tasks_with_google:
                        # Оставляем первую задачу с google_id
                        task_to_keep = tasks_with_google[0]
                        # Объединяем остальные в эту задачу
                        for task_to_merge in tasks_with_google[1:] + tasks_without_google:
                            if task_to_merge.id != task_to_keep.id:
                                logger.info(f"Merging task {task_to_merge.id} into {task_to_keep.id}")
                                # Можно объединить доп. информацию если нужно
                                db.delete(task_to_merge)
                                duplicate_stats["merged"] += 1
                    else:
                        # Нет задач с google_id, оставляем самую старую
                        tasks.sort(key=lambda x: x.id)
                        task_to_keep = tasks[0]
                        for task_to_delete in tasks[1:]:
                            logger.info(f"Deleting duplicate without google_id: {task_to_delete.id}")
                            db.delete(task_to_delete)
                            duplicate_stats["deleted"] += 1

            # Коммитим изменения
            db.commit()

            # Получаем итоговое количество задач
            final_tasks = db.query(Task).filter(
                Task.user_id == uuid.UUID(user_id)
            ).count()

            duplicate_stats["final_task_count"] = final_tasks
            duplicate_stats["removed_total"] = duplicate_stats["deleted"] + duplicate_stats["merged"]

            logger.info(f"=== CLEANUP COMPLETED: "
                        f"Removed {duplicate_stats['removed_total']} duplicates, "
                        f"Final count: {final_tasks} ===")

            return {
                "status": "success",
                "message": "Duplicate cleanup completed",
                "details": duplicate_stats
            }

        except Exception as e:
            logger.error(f"Error in cleanup_duplicate_tasks: {e}")
            db.rollback()
            return {
                "status": "error",
                "message": f"Cleanup failed: {str(e)}",
                "details": {"removed": 0, "error": str(e)}
            }

    def full_cleanup_and_sync(self, db: Session, user_id: str, tasklist_id: str = '@default') -> Dict[str, Any]:
        """Полная очистка дубликатов и синхронизация"""
        try:
            logger.info(f"=== STARTING FULL CLEANUP AND SYNC for user {user_id} ===")

            # 1. Сначала очищаем существующие дубликаты
            cleanup_result = self.cleanup_duplicate_tasks(db, user_id)

            if cleanup_result["status"] == "error":
                logger.error(f"Cleanup failed: {cleanup_result['message']}")
                # Продолжаем синхронизацию несмотря на ошибку очистки

            # 2. Выполняем синхронизацию
            sync_result = self.sync_tasks_from_google(db, user_id, tasklist_id)

            # 3. Объединяем результаты
            combined_result = {
                "status": "success" if cleanup_result["status"] == "success" and sync_result[
                    "status"] == "success" else "partial",
                "message": "Full cleanup and sync completed",
                "cleanup": cleanup_result,
                "sync": sync_result
            }

            logger.info(f"=== FULL CLEANUP AND SYNC COMPLETED ===")
            return combined_result

        except Exception as e:
            logger.error(f"Error in full_cleanup_and_sync: {e}")
            return {
                "status": "error",
                "message": f"Full cleanup and sync failed: {str(e)}",
                "cleanup": {"status": "error", "message": "Not executed"},
                "sync": {"status": "error", "message": "Not executed"}
            }

    def sync_local_to_google(self, db: Session, user_id: str, tasklist_id: str = '@default') -> Dict[str, Any]:
        """Синхронизация локальных изменений в Google Tasks - ИСПРАВЛЕННАЯ ВЕРСИЯ"""
        try:
            logger.info(f"=== SYNC LOCAL → GOOGLE for user {user_id} ===")

            service = self.get_tasks_service(db, user_id)
            if not service:
                return {"status": "error", "message": "Google auth required"}

            # 1. Сначала получаем ВСЕ задачи из Google, чтобы избежать дублирования
            logger.info("Fetching existing tasks from Google...")
            existing_google_tasks = {}
            try:
                google_tasks_result = service.tasks().list(
                    tasklist=tasklist_id,
                    showCompleted=True,
                    showHidden=True,
                    maxResults=1000
                ).execute()

                for google_task in google_tasks_result.get('items', []):
                    google_id = google_task.get('id')
                    if google_id:
                        existing_google_tasks[google_id] = google_task

                logger.info(f"Retrieved {len(existing_google_tasks)} existing tasks from Google")
            except Exception as e:
                logger.error(f"Error fetching Google tasks: {e}")
                existing_google_tasks = {}

            # 2. Получаем локальные задачи
            from app.crud.task import get_tasks_by_user
            local_tasks = get_tasks_by_user(db, user_id)

            # 3. Группируем локальные задачи по google_id
            tasks_with_google_id = {}
            tasks_without_google_id = []

            for task in local_tasks:
                if task.google_task_id:
                    tasks_with_google_id[task.google_task_id] = task
                else:
                    tasks_without_google_id.append(task)

            stats = {
                "created_in_google": 0,
                "updated_in_google": 0,
                "skipped": 0,
                "failed": 0,
                "total_local": len(local_tasks),
                "total_google_before": len(existing_google_tasks)
            }

            # 4. ОБРАБОТКА 1: Обновляем задачи, которые уже есть в Google
            for google_id, local_task in tasks_with_google_id.items():
                try:
                    if google_id in existing_google_tasks:
                        # Задача существует в Google - ОБНОВЛЯЕМ
                        google_task = existing_google_tasks[google_id]

                        # Проверяем, нужно ли обновлять (изменилась ли задача локально)
                        if self._should_update_google_task(local_task, google_task):
                            updated_task = {
                                'title': local_task.title[:1024] if local_task.title else "Untitled",
                                'notes': local_task.description or '',
                                'status': 'completed' if local_task.is_completed else 'needsAction'
                            }

                            # Добавляем due date если есть в локальной задаче
                            if hasattr(local_task, 'due_date') and local_task.due_date:
                                try:
                                    if isinstance(local_task.due_date, datetime):
                                        updated_task['due'] = local_task.due_date.isoformat() + 'Z'
                                    elif isinstance(local_task.due_date, str):
                                        parsed_date = datetime.fromisoformat(local_task.due_date.replace('Z', '+00:00'))
                                        updated_task['due'] = parsed_date.isoformat() + 'Z'
                                except Exception as e:
                                    logger.warning(f"Could not format due date for task {local_task.id}: {e}")

                            service.tasks().update(
                                tasklist=tasklist_id,
                                task=google_id,
                                body=updated_task
                            ).execute()

                            stats["updated_in_google"] += 1
                            logger.info(f"Updated in Google: {local_task.id} - '{local_task.title}'")
                        else:
                            # Нет изменений - пропускаем
                            stats["skipped"] += 1
                    else:
                        # Задача имеет google_id, но не найдена в Google
                        # Это может быть если задача была удалена в Google
                        logger.warning(
                            f"Task {local_task.id} has google_id {google_id} but not found in Google. Clearing...")
                        local_task.google_task_id = None
                        local_task.google_tasklist_id = None
                        # Эта задача попадет в создание ниже
                        tasks_without_google_id.append(local_task)

                except HttpError as e:
                    if e.resp.status == 404:
                        logger.warning(f"Task {local_task.id} not found in Google (404). Clearing google_id...")
                        local_task.google_task_id = None
                        local_task.google_tasklist_id = None
                        tasks_without_google_id.append(local_task)
                    else:
                        stats["failed"] += 1
                        logger.error(f"Google API error for task {local_task.id}: {e}")
                except Exception as e:
                    stats["failed"] += 1
                    logger.error(f"Error processing task {local_task.id}: {e}")

            # 5. ОБРАБОТКА 2: Создаем задачи, которых нет в Google
            # Сначала проверяем на дубликаты по содержимому среди существующих Google задач
            google_tasks_by_content = {}
            for google_task in existing_google_tasks.values():
                content_key = f"{google_task.get('title', '').lower().strip()}|{google_task.get('notes', '').lower().strip()}"
                google_tasks_by_content[content_key] = google_task

            for local_task in tasks_without_google_id:
                try:
                    # Проверяем, нет ли уже такой задачи в Google по содержимому
                    content_key = f"{(local_task.title or '').lower().strip()}|{(local_task.description or '').lower().strip()}"

                    if content_key in google_tasks_by_content:
                        # Нашли дубликат по содержимому - связываем, но не создаем новую
                        existing_google_task = google_tasks_by_content[content_key]
                        google_id = existing_google_task.get('id')

                        local_task.google_task_id = google_id
                        local_task.google_tasklist_id = tasklist_id
                        stats["skipped"] += 1
                        logger.info(f"Linked existing Google task {google_id} to local task {local_task.id}")

                        # Обновляем если нужно
                        if self._should_update_google_task(local_task, existing_google_task):
                            updated_task = {
                                'title': local_task.title[:1024] if local_task.title else "Untitled",
                                'notes': local_task.description or '',
                                'status': 'completed' if local_task.is_completed else 'needsAction'
                            }

                            service.tasks().update(
                                tasklist=tasklist_id,
                                task=google_id,
                                body=updated_task
                            ).execute()
                            stats["updated_in_google"] += 1

                    else:
                        # Создаем новую задачу в Google
                        new_google_task = {
                            'title': local_task.title[:1024] if local_task.title else "Untitled",
                            'notes': local_task.description or '',
                            'status': 'completed' if local_task.is_completed else 'needsAction'
                        }

                        # Добавляем due date если есть
                        if hasattr(local_task, 'due_date') and local_task.due_date:
                            try:
                                if isinstance(local_task.due_date, datetime):
                                    new_google_task['due'] = local_task.due_date.isoformat() + 'Z'
                                elif isinstance(local_task.due_date, str):
                                    parsed_date = datetime.fromisoformat(local_task.due_date.replace('Z', '+00:00'))
                                    new_google_task['due'] = parsed_date.isoformat() + 'Z'
                            except Exception as e:
                                logger.warning(f"Could not format due date for new task {local_task.id}: {e}")

                        result = service.tasks().insert(
                            tasklist=tasklist_id,
                            body=new_google_task
                        ).execute()

                        google_id = result.get('id')
                        local_task.google_task_id = google_id
                        local_task.google_tasklist_id = tasklist_id
                        stats["created_in_google"] += 1
                        logger.info(f"Created in Google: {local_task.id} - '{local_task.title}' (ID: {google_id})")

                    # Обновляем timestamp синхронизации
                    local_task.synced_with_google_at = datetime.utcnow()

                except Exception as e:
                    stats["failed"] += 1
                    logger.error(f"Error creating task {local_task.id} in Google: {e}")

            db.commit()

            # 6. Формируем результат
            total_successful = stats["created_in_google"] + stats["updated_in_google"]

            if total_successful == 0 and stats["failed"] > 0:
                status_val = "error"
                message = f"All {stats['failed']} tasks failed"
            elif stats["failed"] > 0:
                status_val = "partial"
                message = f"{total_successful} tasks processed, {stats['failed']} failed"
            else:
                status_val = "success"
                message = f"Successfully synced {total_successful} tasks to Google"

            logger.info(f"=== LOCAL → GOOGLE COMPLETED: "
                        f"Created: {stats['created_in_google']}, "
                        f"Updated: {stats['updated_in_google']}, "
                        f"Skipped: {stats['skipped']}, "
                        f"Failed: {stats['failed']} ===")

            return {
                "status": status_val,
                "message": message,
                "details": stats
            }

        except Exception as e:
            logger.error(f"Error in sync_local_to_google: {e}")
            db.rollback()
            return {
                "status": "error",
                "message": f"Sync to Google failed: {str(e)}",
                "details": {"created": 0, "updated": 0, "failed": 0}
            }

    def _should_update_google_task(self, local_task, google_task: Dict[str, Any]) -> bool:
        """Определить, нужно ли обновлять задачу в Google"""
        # 1. Проверяем заголовок
        google_title = google_task.get('title', '')
        if google_title != (local_task.title or ''):
            return True

        # 2. Проверяем описание
        google_notes = google_task.get('notes', '')
        if google_notes != (local_task.description or ''):
            return True

        # 3. Проверяем статус выполнения
        google_status = google_task.get('status', 'needsAction')
        local_is_completed = bool(local_task.is_completed)
        google_is_completed = google_status == 'completed'

        if local_is_completed != google_is_completed:
            return True

        # 4. Проверяем due date
        google_due = google_task.get('due')
        if hasattr(local_task, 'due_date') and local_task.due_date:
            try:
                if google_due:
                    google_due_dt = datetime.fromisoformat(google_due.replace('Z', '+00:00'))
                    if isinstance(local_task.due_date, datetime):
                        return local_task.due_date != google_due_dt
                    elif isinstance(local_task.due_date, str):
                        local_due_dt = datetime.fromisoformat(local_task.due_date.replace('Z', '+00:00'))
                        return local_due_dt != google_due_dt
                else:
                    # В Google нет due date, а локально есть
                    return True
            except Exception:
                # Если ошибка парсинга дат - считаем что нужно обновить
                return True
        elif google_due:
            # В Google есть due date, а локально нет
            return True

        # 5. Проверяем время последнего изменения
        if local_task.synced_with_google_at:
            if hasattr(local_task, 'updated_at') and local_task.updated_at:
                if local_task.updated_at > local_task.synced_with_google_at:
                    return True

        return False

    
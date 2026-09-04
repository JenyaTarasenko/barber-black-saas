import uuid
from django.contrib.auth.base_user import AbstractBaseUser
from django.contrib.auth.models import BaseUserManager, PermissionsMixin
from django.db import models


class UserManager(BaseUserManager):
    """
    Менеджер пользователей.

    Отвечает за:
    - создание обычного пользователя;
    - создание суперпользователя;
    - нормализацию email;
    - установку пароля.
    """

    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError("Email is required")

        email = self.normalize_email(email)

        user = self.model(
            email=email,
            **extra_fields,
        )

        user.set_password(password)
        user.save(using=self._db)

        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        extra_fields.setdefault("is_active", True)

        return self.create_user(
            email=email,
            password=password,
            **extra_fields,
        )


class User(AbstractBaseUser, PermissionsMixin):
    """
    Пользователь системы.

    User — это аккаунт для входа в SaaS.
    Сам по себе User не является салоном, владельцем
    или мастером. Связи с бизнесом появятся отдельно.
    """

    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
    )

    email = models.EmailField(
        unique=True,
        db_index=True,
    )

    phone = models.CharField(
        max_length=32,
        blank=True,
    )

    first_name = models.CharField(
        max_length=100,
        blank=True,
    )

    last_name = models.CharField(
        max_length=100,
        blank=True,
    )

    is_active = models.BooleanField(
        default=True,
    )

    is_staff = models.BooleanField(
        default=False,
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
    )

    updated_at = models.DateTimeField(
        auto_now=True,
    )

    objects = UserManager()

    USERNAME_FIELD = "email"

    class Meta:
        db_table = "users"

    def __str__(self):
        return self.email


"""
===============================================================================
                       КАК РАБОТАЕТ АУТЕНТИФИКАЦИЯ И МОДЕЛЬ USER
===============================================================================

1. АРХИТЕКТУРНАЯ ИДЕЯ (Разделение ответственности):
-------------------------------------------------------------------------------
Модель `User` отвечает ТОЛЬКО за вход в систему (аутентификацию) и безопасность:
- Хранит учётные данные: Email и Хеш пароля (сам пароль никогда не хранится открытым!).
- Управляет статусом аккаунта (активен/заблокирован) и правами доступа в админку (is_staff).
- НЕ СОДЕРЖИТ бизнес-логику салона (цены, услуги, записи, проценты мастеров).
  Вся бизнес-логика выносится в отдельные модели (напр. Salon, MasterProfile). 
  Благодаря этому один User в будущем сможет быть, например, мастером в одном 
  салоне и владельцем в другом.

2. ДЛЯ ЧЕГО НУЖЕН UserManager (Менеджер пользователей):
-------------------------------------------------------------------------------
Стандартный менеджер Django (`objects.create()`) создает пользователей с ОПЕН-ТЕКСТОВЫМ 
паролем и ищет пользователя по полю `username`. 

Наш кастомный `UserManager` переопределяет это поведение:
а) `normalize_email()` — примет `User@Gmail.com` и приведёт к `user@gmail.com` 
   (защита от дубликатов из-за регистра).
б) `set_password(password)` — берет сырой пароль ("124563456") и превращает его 
   в защищенный хэш (например, "pbkdf2_sha256$...") перед записью в БД.
в) `create_user()` — точка создания обычных юзеров из API (регистрация).
г) `create_superuser()` — точка создания администраторов через консоль (`createsuperuser`).

3. ПУТЬ ДАННЫХ (ОТ КЛИЕНТА ДО БД И ОБРАТНО В JSON):
-------------------------------------------------------------------------------
Шаг 1 [Next.js (Фронтенд)]:
   Пользователь вводит email и пароль и отправляет POST-запрос на `/api/accounts/register/`.

Шаг 2 [DRF Serializer (Сериализатор)]:
   Сериализатор валидирует данные (проверяет, уникален ли email, надежен ли пароль).
   В методе `create()` сериализатор вызывает именно `User.objects.create_user(**validated_data)`, 
   передавая задачу создания менеджеру.

Шаг 3 [UserManager + Database (База данных)]:
   Менеджер шифрует пароль, генерирует UUID для поля `id` и сохраняет строку в таблицу `users`.

Шаг 4 [Генерация ответа (JSON)]:
   Сериализатор берет созданный объект `User`, выбирает только разрешенные поля 
   (id, email, first_name, last_name, phone) — ИСКЛЮЧАЯ пароль! — 
   и превращает их в JSON-ответ для Next.js.

4. КЛЮЧЕВЫЕ ПОЛЯ МОДЕЛИ USER:
-------------------------------------------------------------------------------
- `id (UUIDField)`: Вместо обычных цифр (1, 2, 3) используется UUID (напр. 9b1deb4d-3b7d...). 
  Это нужно для безопасности в SaaS: злоумышленники не смогут перебрать id пользователей.
- `USERNAME_FIELD = "email"`: Сообщает Django, что логином для входа является Email, а не Username.
- `db_table = "users"`: Явно задает красивое имя таблицы в PostgreSQL вместо `accounts_user`.
===============================================================================
"""

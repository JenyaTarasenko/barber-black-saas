6. Этап 1 — ядро SaaS

Создаём:

User
Salon
SalonMembership

Получаем:

User
  │
  ▼
SalonMembership
  │
  ├── Salon
  └── Role

Проверяем:

User создаётся
Salon создаётся
Membership создаётся
Role работает
User может принадлежать Salon

Пишем тесты.

Только когда:

python manage.py test

OK

переходим дальше.

7. Этап 2 — филиалы и сотрудники

Добавляем:

Branch
Employee
EmployeeBranch

Теперь:

Salon
│
├── Branch
│
└── Employee
       │
       └── EmployeeBranch

Проверяем:

Salon A
 ├── Kyiv
 └── Odesa

Salon B
 └── Lviv

И тест:

Employee Salon A не может оказаться в Branch Salon B.

Это уже первый настоящий multi-tenant тест.

8. Этап 3 — услуги

Добавляем:

ServiceCategory
Service
EmployeeService

Получаем:

Salon
│
├── Employees
│
└── Services
      │
      └── EmployeeService

Проверяем:

Alex → Haircut
Alex → Beard

John → Haircut

И тестируем:

John не может быть назначен на услугу, которую он не оказывает.

9. Этап 4 — расписание

Добавляем:

Schedule
ScheduleBreak

Например:

Alex

Monday
09:00 — 18:00

Break
13:00 — 14:00

Теперь пишем бизнес-тесты:

10:00 → можно
12:00 → можно
13:30 → нельзя
18:30 → нельзя
10. Этап 5 — Client

Теперь:

Client
LoyaltyLevel

И очень важно:

Client → Salon

То есть:

Salon A
├── Client Anna
└── Client Alex

Salon B
└── Client John

Тест:

Salon A
не видит
Client John
11. Этап 6 — Appointment

И только после всего этого создаём:

Appointment
AppointmentService
AppointmentStatusHistory

Потому что теперь у нас уже существуют:

Salon
Branch
Employee
Service
Client
Schedule

И Appointment просто связывает их.

                    Appointment
                         │
       ┌─────────────────┼──────────────────┐
       ▼                 ▼                  ▼
     Client           Employee            Branch
                         │
                         ▼
                       Service
12. Appointment будет самым тестируемым местом

Потому что здесь много бизнес-правил.

Например:

Тест №1
Employee принадлежит Salon A
Appointment принадлежит Salon B

→ FAIL
Тест №2
Employee Alex
Branch Kyiv

Appointment
Branch Odesa

→ FAIL
Тест №3
Alex не оказывает Coloring

Appointment → Coloring

→ FAIL
Тест №4
Alex работает:

09:00–18:00

Appointment:
20:00

→ FAIL
Тест №5
Appointment:
13:30

Break:
13:00–14:00

→ FAIL
Тест №6
Alex:

10:00–11:00 Appointment

новая запись:

10:30–11:30

→ FAIL

Вот здесь уже начинается настоящий backend.

13. Очень важное правило: миграция ≠ архитектура

Это тоже нужно запомнить.

Когда мы пишем:

python manage.py makemigrations

Django генерирует техническое изменение БД.

Но мы не должны использовать миграции как способ проектирования.

Сначала:

Архитектура
↓
Модели
↓
Проверка моделей
↓
Migration

А не:

Migration
↓
посмотрим что получилось
↓
ой, неправильно
↓
ещё migration
14. Когда можно менять архитектуру?

Можно.

Наоборот, в начале проекта менять архитектуру нормально.

Например мы сегодня решили:

Employee → User

А через неделю поняли:

Нет, Employee должен быть отдельно.

Мы меняем модель до того, как система стала огромной.

Поэтому сейчас самое время думать.

Но после того как появятся:

тысячи пользователей
данные
production
реальные клиенты

изменения становятся намного дороже.

15. Как будем работать конкретно с тобой

Вот это я предлагаю сделать нашим постоянным процессом.

Ты говоришь:

Делаем Branch.

Я отвечаю:

ШАГ 1
Что такое Branch

ШАГ 2
Какие поля нужны

ШАГ 3
Как он связан с Salon

ШАГ 4
Пишем модель

ШАГ 5
Admin

ШАГ 6
Migration

ШАГ 7
Tests

ШАГ 8
Запускаем

ШАГ 9
Разбираем результат

Ты выполняешь.

Например показываешь:

python manage.py test

FAILED...

И мы не идём дальше, пока не разберём ошибку.
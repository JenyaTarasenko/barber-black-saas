accounts
└── User

tenants 
├── Salon
├── Role
└── SalonMembership

branches
└── Branch

employees
├── Employee
└── EmployeeBranch

services
├── ServiceCategory
├── Service
└── EmployeeService

schedules
├── Schedule
└── ScheduleBreak

clients
├── LoyaltyLevel
└── Client

appointments
├── Appointment
├── AppointmentService
└── AppointmentStatusHistory


MODELS DOCUMENTATION — full schema
1. APP: accounts
Model: User | Table: users
Поле	Тип	Настройки
id	UUIDField	primary_key=True, default=uuid4, editable=False
email	EmailField	unique=True, db_index=True
phone	CharField(32)	blank=True
first_name	CharField(100)	blank=True
last_name	CharField(100)	blank=True
is_active	BooleanField	default=True
is_staff	BooleanField	default=False
created_at	DateTimeField	auto_now_add=True
updated_at	DateTimeField	auto_now=True
password	CharField(128)	—
last_login	DateTimeField	null=True, blank=True
groups	ManyToManyField	—
user_permissions	ManyToManyField	—
Внешние связи: нет
2. APP: tenants
Model: Salon | Table: salons
Поле	Тип	Настройки
id	UUIDField	primary_key=True, default=uuid4, editable=False
name	CharField(255)	—
slug	SlugField	unique=True, db_index=True
phone	CharField(32)	blank=True
email	EmailField	blank=True
is_active	BooleanField	default=True
created_at	DateTimeField	auto_now_add=True
updated_at	DateTimeField	auto_now=True
Внешние связи: нет
Обратные связи: memberships, branches, employees, service_categories, services, clients, appointments, loyalty_levels
Model: Role | Table: roles
Поле	Тип	Настройки
id	UUIDField	primary_key=True, default=uuid4, editable=False
code	CharField(50)	unique=True
name	CharField(100)	—
description	TextField	blank=True
Внешние связи: нет
Значения code: PLATFORM_ADMIN, OWNER, BRANCH_ADMIN, MASTER
Model: SalonMembership | Table: salon_memberships
Поле	Тип	Настройки
id	UUIDField	primary_key=True, default=uuid4, editable=False
user	FK	on_delete=CASCADE
salon	FK	on_delete=CASCADE
role	FK	on_delete=PROTECT
is_active	BooleanField	default=True
created_at	DateTimeField	auto_now_add=True
updated_at	DateTimeField	auto_now=True
Внешние связи:
user → User
salon → Salon
role → Role
Constraints: UniqueConstraint(fields=["user", "salon"], name="unique_user_salon_membership")
3. APP: branch
Model: Branch | Table: branches
Поле	Тип	Настройки
id	UUIDField	primary_key=True, default=uuid4, editable=False
salon	FK	on_delete=CASCADE
name	CharField(255)	—
address	CharField(500)	blank=True
phone	CharField(32)	blank=True
is_active	BooleanField	default=True
created_at	DateTimeField	auto_now_add=True
updated_at	DateTimeField	auto_now=True
Внешние связи:
salon → Salon
4. APP: employee
Model: Employee | Table: employees
Поле	Тип	Настройки
id	UUIDField	primary_key=True, default=uuid4, editable=False
salon	FK	on_delete=CASCADE
first_name	CharField(100)	—
last_name	CharField(100)	blank=True
phone	CharField(32)	blank=True
email	EmailField	blank=True
is_active	BooleanField	default=True
created_at	DateTimeField	auto_now_add=True
updated_at	DateTimeField	auto_now=True
Внешние связи:
salon → Salon
Model: EmployeeBranch | Table: employee_branches
Поле	Тип	Настройки
id	UUIDField	primary_key=True, default=uuid4, editable=False
employee	FK	on_delete=CASCADE
branch	FK	on_delete=CASCADE
is_active	BooleanField	default=True
created_at	DateTimeField	auto_now_add=True
updated_at	DateTimeField	auto_now=True
Внешние связи:
employee → Employee
branch → Branch
Constraints: UniqueConstraint(fields=["employee", "branch"], name="unique_employee_branch")
5. APP: services
Model: ServiceCategory | Table: service_categories
Поле	Тип	Настройки
id	UUIDField	primary_key=True, default=uuid4, editable=False
salon	FK	on_delete=CASCADE
name	CharField(255)	—
description	TextField	blank=True
is_active	BooleanField	default=True
created_at	DateTimeField	auto_now_add=True
updated_at	DateTimeField	auto_now=True
Внешние связи:
salon → Salon
Model: Service | Table: services
Поле	Тип	Настройки
id	UUIDField	primary_key=True, default=uuid4, editable=False
salon	FK	on_delete=CASCADE
category	FK	on_delete=CASCADE
name	CharField(255)	—
description	TextField	blank=True
price	DecimalField(10,2)	—
duration_minutes	PositiveIntegerField	—
is_active	BooleanField	default=True
created_at	DateTimeField	auto_now_add=True
updated_at	DateTimeField	auto_now=True
Внешние связи:
salon → Salon
category → ServiceCategory
Model: EmployeeService | Table: employee_services
Поле	Тип	Настройки
id	UUIDField	primary_key=True, default=uuid4, editable=False
employee	FK	on_delete=CASCADE
service	FK	on_delete=CASCADE
is_active	BooleanField	default=True
created_at	DateTimeField	auto_now_add=True
updated_at	DateTimeField	auto_now=True
Внешние связи:
employee → Employee
service → Service
Constraints: UniqueConstraint(fields=["employee", "service"], name="unique_employee_service")
6. APP: clients
Model: LoyaltyLevel | Table: loyalty_levels
Поле	Тип	Настройки
id	UUIDField	primary_key=True, default=uuid4, editable=False
salon	FK	on_delete=CASCADE
name	CharField(100)	—
min_visits	PositiveIntegerField	default=0
discount_percent	DecimalField(5,2)	default=0
is_active	BooleanField	default=True
created_at	DateTimeField	auto_now_add=True
updated_at	DateTimeField	auto_now=True
Внешние связи:
salon → Salon
Constraints: UniqueConstraint(fields=["salon", "name"], name="unique_salon_loyalty_level_name")
Model: Client | Table: clients
Поле	Тип	Настройки
id	UUIDField	primary_key=True, default=uuid4, editable=False
salon	FK	on_delete=CASCADE
loyalty_level	FK	on_delete=SET_NULL, null=True, blank=True
first_name	CharField(100)	—
last_name	CharField(100)	blank=True
phone	CharField(32)	—
email	EmailField	blank=True
notes	TextField	blank=True
is_active	BooleanField	default=True
created_at	DateTimeField	auto_now_add=True
updated_at	DateTimeField	auto_now=True
Внешние связи:
salon → Salon
loyalty_level → LoyaltyLevel
Constraints: UniqueConstraint(fields=["salon", "phone"], name="unique_salon_client_phone")
7. APP: appointments
Model: Appointment | Table: appointments
Поле	Тип	Настройки
id	UUIDField	primary_key=True, default=uuid4, editable=False
salon	FK	on_delete=CASCADE
client	FK	on_delete=PROTECT
employee	FK	on_delete=PROTECT
branch	FK	on_delete=PROTECT
start_datetime	DateTimeField	—
end_datetime	DateTimeField	—
status	CharField(20)	default="CREATED"
client_notes	TextField	blank=True
internal_notes	TextField	blank=True
created_by	FK	on_delete=SET_NULL, null=True, blank=True
created_at	DateTimeField	auto_now_add=True
updated_at	DateTimeField	auto_now=True
Внешние связи:
salon → Salon
client → Client
employee → Employee
branch → Branch
created_by → User
Значения status: CREATED, CONFIRMED, IN_PROGRESS, COMPLETED, CANCELLED, NO_SHOW
Ordering: ["start_datetime"]
Model: AppointmentService | Table: appointment_services
Поле	Тип	Настройки
id	UUIDField	primary_key=True, default=uuid4, editable=False
appointment	FK	on_delete=CASCADE
service	FK	on_delete=PROTECT
price	DecimalField(10,2)	—
duration_minutes	PositiveIntegerField	—
created_at	DateTimeField	auto_now_add=True
Внешние связи:
appointment → Appointment
service → Service
Model: AppointmentStatusHistory | Table: appointment_status_history
Поле	Тип	Настройки
id	UUIDField	primary_key=True, default=uuid4, editable=False
appointment	FK	on_delete=CASCADE
status	CharField(20)	—
changed_by	FK	on_delete=SET_NULL, null=True, blank=True
comment	TextField	blank=True
created_at	DateTimeField	auto_now_add=True
Внешние связи:
appointment → Appointment
changed_by → User
Ordering: ["created_at"]
8. APP: schedules
Model: Schedule | Table: schedules
Поле	Тип	Настройки
id	UUIDField	primary_key=True, default=uuid4, editable=False
employee	FK	on_delete=CASCADE
branch	FK	on_delete=CASCADE
weekday	PositiveSmallIntegerField	choices
start_time	TimeField	—
end_time	TimeField	—
is_active	BooleanField	default=True
created_at	DateTimeField	auto_now_add=True
updated_at	DateTimeField	auto_now=True
Внешние связи:
employee → Employee
branch → Branch
Constraints: UniqueConstraint(fields=["employee", "branch", "weekday"], name="unique_employee_branch_weekday_schedule")
Значения weekday: 0=MONDAY … 6=SUNDAY
⚠️ Нет salon FK
Model: ScheduleBreak | Table: schedule_breaks
Поле	Тип	Настройки
id	UUIDField	primary_key=True, default=uuid4, editable=False
schedule	FK	on_delete=CASCADE
start_time	TimeField	—
end_time	TimeField	—
created_at	DateTimeField	auto_now_add=True
updated_at	DateTimeField	auto_now=True
Внешние связи:
schedule → Schedule
ALL FOREIGN KEYS — cross-tenant map
#	Модель	Поле FK	→ Целевая модель
1	SalonMembership	user	User
2	SalonMembership	salon	Salon
3	SalonMembership	role	Role
4	Branch	salon	Salon
5	Employee	salon	Salon
6	EmployeeBranch	employee	Employee
7	EmployeeBranch	branch	Branch
8	ServiceCategory	salon	Salon
9	Service	salon	Salon
10	Service	category	ServiceCategory
11	EmployeeService	employee	Employee
12	EmployeeService	service	Service
13	LoyaltyLevel	salon	Salon
14	Client	salon	Salon
15	Client	loyalty_level	LoyaltyLevel
16	Appointment	salon	Salon
17	Appointment	client	Client
18	Appointment	employee	Employee
19	Appointment	branch	Branch
20	Appointment	created_by	User
21	AppointmentService	appointment	Appointment
22	AppointmentService	service	Service
23	AppointmentStatusHistory	appointment	Appointment
24	AppointmentStatusHistory	changed_by	User
25	Schedule	employee	Employee
26	Schedule	branch	Branch
27	ScheduleBreak	schedule	Schedule
JOIN TABLES (промежуточные таблицы)
#	Таблица	Модель	Связывает
1	salon_memberships	SalonMembership	User ↔ Salon (+ Role)
2	employee_branches	EmployeeBranch	Employee ↔ Branch
3	employee_services	EmployeeService	Employee ↔ Service
4	appointment_services	AppointmentService	Appointment ↔ Service
5	schedules	Schedule	Employee ↔ Branch (+ weekday)
6	schedule_breaks	ScheduleBreak	Schedule (+ time range)
СВОДНАЯ СТАТИСТИКА
Значение
8
15
17 (User + 16 из db_table)
27
7 (Branch, Employee, ServiceCategory, Service, LoyaltyLevel, Client, Appointment)
12 (EmployeeBranch, EmployeeService, Service→Category, Client→LoyaltyLevel, Appointment→Client/Employee/Branch, AppointmentService→Service, Schedule→Employee/Branch)
6 (User ×3, Role, Schedule, ScheduleBreak)
2 (User.groups, User.user_permissions)
6
0
3 (User, Role, Schedule)
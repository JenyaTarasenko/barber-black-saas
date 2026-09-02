| Entity | Назначение | Parent | Владелец |
|--------|------------|--------|----------|
| Salon | Бизнес | — | — |
| Branch | Филиал | Salon | Salon |
| User | Аккаунт | — | — |
| Membership | Доступ User к Salon | User + Salon | Salon |
| Employee | Сотрудник | Salon | Salon |
| Service | Услуга | Salon | Salon |
| Client | Клиент | Salon | Salon |
| Appointment | Запись | Salon | Salon |

----------------------------------------

## Relationships

Salon
 ├── Branch
 ├── Membership
 ├── Employee
 ├── Service
 ├── Client
 └── Appointment

Employee
 ├── EmployeeBranch
 ├── EmployeeService
 └── Schedule

Appointment
 ├── Client
 ├── Employee
 ├── Branch
 ├── AppointmentService
 └── AppointmentStatusHistory


 
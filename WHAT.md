1 Сначала делаю Account
accounts
└── User
    ├── email
    ├── password
    ├── phone
    ├── first_name
    └── last_name

сделал тесты 
2 Сделал Tenant (роли)



tenants
├── Salon                       
└── SalonMembership 

3 Branch 
Branch — конкретное место/филиал этого бизнеса.

сотудники
Employee один сотрудник один фелиал 
      │
      └── User
            └── email + password


EmployeeBranch - много сотрудников много фелиалов



услуги салона


#!/usr/bin/env python3

import sys
from database import Database

def main():
    if len(sys.argv) != 2:
        print("Использование: python add_admin.py YOUR_TELEGRAM_ID")
        print("Пример: python add_admin.py 123456789")
        sys.exit(1)
    
    try:
        telegram_id = int(sys.argv[1])
    except ValueError:
        print("Ошибка: ID должен быть числом")
        sys.exit(1)
    
    db = Database()
    
    if db.is_admin(telegram_id):
        print(f"Пользователь {telegram_id} уже является администратором")
        sys.exit(0)
    
    db.add_admin(telegram_id)
    print(f"Пользователь {telegram_id} добавлен в администраторы")
    
    admins = db.get_all_admins()
    print(f"\nВсего администраторов: {len(admins)}")
    for admin_id in admins:
        print(f"  - {admin_id}")

if __name__ == '__main__':
    main()
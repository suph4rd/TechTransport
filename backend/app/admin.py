"""Usage: python -m app.admin +375291234567"""
import argparse
from sqlalchemy import select
from app.auth.validators import normalize_phone
from app.core.db import SessionLocal
from app.auth.models import User


def main():
    parser = argparse.ArgumentParser(description="Назначить администратора (пользователь должен сначала войти)")
    parser.add_argument("phone", type=normalize_phone)
    args = parser.parse_args()
    with SessionLocal() as db:
        user = db.scalar(select(User).where(User.phone == args.phone))
        if not user:
            parser.error("Пользователь не найден: сначала выполните вход")
        if not user.is_active:
            parser.error("Аккаунт отключён")
        user.role = "admin"
        db.commit()
        print("Права администратора назначены")


if __name__ == "__main__":
    main()

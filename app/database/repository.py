from typing import Optional, Dict
from app.models.schemas.user_schema import UserInDB


class UserRepository:

    def __init__(self):
        self.user_db: Dict[str, dict] = {}

    def get_user_by_email(self, email: str) -> Optional[dict]:
        if email in self.user_db:
            user_dict = self.user_db[email]
            return UserInDB(**user_dict)
        return None


    def create_user(self, user: UserInDB) -> UserInDB:
        self.user_db[user.email] = user.model_dump()
        return user
    
    def email_exist(self, email: str) -> bool:
        return email in self.user_db
    
    def get_all_users(self) -> Dict[str, dict]:
        return self.user_db
    
user_repository = UserRepository()
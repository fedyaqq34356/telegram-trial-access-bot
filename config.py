import os
from dataclasses import dataclass

@dataclass
class Config:
    bot_token: str
    work_chat_id: int
    study_group_id: int
    trial_minutes: int = 11520
    crm_api_base: str = 'http://127.0.0.1:8000/api'
    internal_api_token: str = ''

    @classmethod
    def from_env(cls):
        return cls(
            bot_token=os.getenv('BOT_TOKEN'),
            work_chat_id=int(os.getenv('WORK_CHAT_ID')),
            study_group_id=int(os.getenv('STUDY_GROUP_ID')),
            trial_minutes=int(os.getenv('TRIAL_MINUTES', '11520')),
            crm_api_base=os.getenv('CRM_API_BASE', 'http://127.0.0.1:8000/api'),
            internal_api_token=os.getenv('INTERNAL_API_TOKEN', ''),
        )
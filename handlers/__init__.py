from aiogram import Router

from . import chat_events
from . import menu_handlers
from . import admin_handlers
from . import agency_handlers
from . import callback_handlers
from . import check_handlers
from . import application_handlers

router = Router()

router.include_router(chat_events.router)
router.include_router(menu_handlers.router)
router.include_router(admin_handlers.router)
router.include_router(agency_handlers.router)
router.include_router(callback_handlers.router)
router.include_router(check_handlers.router)
router.include_router(application_handlers.router)
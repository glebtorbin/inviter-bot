from db.base import database

from .clientRepo import ClientRepo
from .memberRepo import MemberRepo
from .proxyRepo import ProxyRepo
from .userRepo import UserRepo
from .channelRepo import ChannelRepo
from .reportPlanRepo import ReportRepo, PlanRepo
from .channelClientRepo import ChannelClientRepo, ChannelSourceRepo
from .WAClientRepo import WaClientRepo


def get_client_repo() -> ClientRepo:
    """ `Row` filds: `id`, `work_id`, `status_id`, `api_id`, `api_hash`, `phone`, `created_at`"""
    return ClientRepo(database)


def get_user_repo() -> UserRepo:
    """ `Row` filds: `id`, `first_name`, `last_name`, `username`, `role_id`, `created_at` """
    return UserRepo(database)


def get_member_repo() -> MemberRepo:
    """ `Row` filds: `id`, `first_name`, `last_name`, `username`, `chat_id`, `created_at` """
    return MemberRepo(database)


def get_proxy_repo() -> ProxyRepo:
    return ProxyRepo(database)


def get_channel_repo() -> ChannelRepo:
    return ChannelRepo(database)


def get_report_repo() -> ReportRepo:
    return ReportRepo(database)

def get_plan_repo() -> PlanRepo:
    return PlanRepo(database)

def get_channel_client_repo() -> ChannelClientRepo:
    return ChannelClientRepo(database)

def get_source_repo() -> ChannelSourceRepo:
    return ChannelSourceRepo(database)

def get_wa_client_repo() -> WaClientRepo:
    return WaClientRepo(database)


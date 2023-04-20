from aiogram.dispatcher.filters.state import State, StatesGroup


class GlobalState(StatesGroup):
    admin = State()
    set_api_id = State()
    set_api_hash = State()
    set_phone = State()
    set_acc_func = State()
    wa_instance = State()
    wa_token = State()
    wa_send_qr = State()
    wa_mailing_file = State()
    wa_mailing_correct_file = State()
    wa_mailing_cor_text = State()
    wa_mailing_message = State()

    add_proxy = State()

    auth_acc = State()

    start_ch_scrap = State()
    lang_choice = State()

    search_open_chat = State()
    second_search = State()

    send_client_chat = State()

    test = State()
    group_choice = State()
    scrap = State()
    add_triggers = State()
    save_triggers = State()
    region_choice = State()

    # keywords = State()
class ClientState(StatesGroup):
    accept = State()
    client = State()
    send_phone_code = State()
    enter_code = State()
    about_1 = State()
    about_2 = State()
    about_3 = State()
    cur_choice = State()
    paym_confirm = State()
    check_paym = State()
    mark_nps = State()
    pay_mems = State()
    add_group_to_sources = State()

    accept_bot = State()
    send_client_chat = State()
    accept_client_acc = State()
    wait_end_add_channle = State()

    wait_link_pars = State()
    wait_end_link_pars = State()

    choice_group_profile = State()
    choice_group_pars = State()
    dop_state = State()
    on_invite = State()
    off_invite = State()
    change_group = State()

    wait_setting_group = State()
    choice_source_add = State()
    choice_source_del = State()
user_modes: dict = {}        # admin_id -> mode string
admin_check_mode: set = set()  # admin_ids in "check ID" mode
pending_tfa: dict = {}       # admin_id -> {anchor_id, user_tg_id, user_username, agency_name}
tfa_waitlist: dict = {}      # agency_name -> list of {anchor_id, user_tg_id, user_username}

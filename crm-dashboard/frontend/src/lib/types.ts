export interface Me {
  id: number;
  username: string;
  name: string;
  role: string;
  is_superadmin: boolean;
  can_manage_users: boolean;
  can_view_traffic: boolean;
  accessible_agency_ids: number[];
}

export interface Agency {
  id: number;
  name: string;
  url: string;
  tfa_required: boolean;
  is_active: boolean;
  has_session: boolean;
  last_synced_at: string | null;
  cooldown_remaining_seconds: number;
  can_change_ratio: boolean;
  can_split: boolean;
}

export interface Host {
  id: number;
  agency_id: number;
  agency_name: string;
  display_account_id: string;
  nickname: string;
  avatar_url: string;
  agent_name: string;
  ratio: number;
  ratio_percent: number;
  down_rate: number;
  real_down_rate: number;
  receive_rate: number;
  monthly_income: number;
  monthly_income_usd: number;
  last_day_income: number;
  last_day_income_usd: number;
  
  month_income_host: number;
  month_income_host_usd: number;
  last_day_income_host: number;
  last_day_income_host_usd: number;
  
  month_income_agency: number;
  month_income_agency_usd: number;
  last_day_income_agency: number;
  last_day_income_agency_usd: number;
  is_blocked: boolean;
  ban_status: string;
  monthly_online: string;
  last_day_online: string;
  approval_date: string;
  balance_coins: number;
  split_diamond: number;
  monthly_income_ranking: number | null;
  grade: string;
  grade_emoji: string;
  grade_color: string;
  grade_range: string;
  grade_limit: number | null;
  punishment: string | null;
  risk_status: "safe" | "warning" | "danger";
  risk_reason: string;
  risk_excess: number | null;
}

export interface Paged<T> {
  items: T[];
  total: number;
  page: number;
  limit: number;
}

export interface AccessOut {
  agency_id: number;
  agency_name: string;
  can_view: boolean;
  can_change_ratio: boolean;
  can_split: boolean;
}

export interface CrmUser {
  id: number;
  username: string;
  name: string;
  role: string;
  can_manage_users: boolean;
  can_view_traffic: boolean;
  is_active: boolean;
  created_at: string | null;
  last_login: string | null;
  accesses: AccessOut[];
}

export interface TrafficKV { key: string; count: number }

export interface TrafficStats {
  range_days: number;
  totals: {
    visits: number;
    uniques: number;
    applications: number;
    conversion_rate: number;
    visits_prev: number;
    visits_delta_percent: number | null;
  };
  daily: { date: string; visits: number; uniques: number }[];
  sources: TrafficKV[];
  campaigns: TrafficKV[];
  top_pages: TrafficKV[];
  devices: TrafficKV[];
  conversion_by_source: { source: string; visits: number; applications: number; rate: number }[];
}

export interface SplitOp {
  id: number;
  scope_label: string;
  agency_id: number | null;
  processed: number;
  skipped: number;
  errors: number;
  total_amount_coins: number;
  total_amount_usd: number;
  agency_amount_coins: number;
  agency_amount_usd: number;
  host_amount_coins: number;
  host_amount_usd: number;
  status: string;
  details?: any;
  started_at: string | null;
  finished_at: string | null;
  duration_seconds: number;
}

export interface ApplicationStatusEvent {
  id: number;
  old_status: string;
  old_status_label: string;
  new_status: string;
  new_status_label: string;
  actor: string;
  note: string;
  created_at: string | null;
}

export interface Application {
  id: number;
  created_at: string | null;
  age: number;
  country: string;
  contact_telegram: string;
  contact_whatsapp: string;
  contact_display: string;
  email: string;
  experience: boolean;
  experience_apps: string;
  time_commitment: string;
  photos_count: number;
  status: string;
  status_label: string;
  manager_comment: string;
  source: string;
  events?: ApplicationStatusEvent[];
}

export interface StatusOption { value: string; label: string }

export interface Testimonial {
  id: number;
  is_visible: boolean;
  sort_order: number;
  lang: string;
  flag: string;
  country: string;
  age: number;
  week: string;
  month: string;
  date: string;
  msg_in: string;
  msg_reply: string;
  time_in: string;
  time_reply: string;
  created_at: string | null;
}

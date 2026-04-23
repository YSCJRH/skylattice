create table if not exists control_plane_users (
  user_id text primary key,
  github_login varchar(128) not null,
  email varchar(320),
  created_at timestamptz not null
);

create table if not exists paired_devices (
  device_id uuid primary key,
  user_id text not null,
  label varchar(160) not null,
  bridge_base_url text not null,
  connector_token text not null,
  last_seen_at timestamptz,
  online boolean not null,
  latest_kernel_status varchar(32),
  latest_auth_summary text
);

create table if not exists pairing_challenges (
  pairing_id uuid primary key,
  user_id text not null,
  pairing_code varchar(24) not null,
  created_at timestamptz not null,
  expires_at timestamptz not null,
  claimed_at timestamptz,
  device_id uuid,
  device_label varchar(160),
  connector_token text
);

create table if not exists command_requests (
  command_id uuid primary key,
  user_id text not null,
  device_id uuid,
  kind varchar(64) not null,
  status varchar(32) not null,
  created_at timestamptz not null,
  updated_at timestamptz not null,
  claimed_at timestamptz,
  payload jsonb not null,
  result jsonb,
  error text
);

create table if not exists approval_records (
  approval_id uuid primary key,
  user_id text not null,
  summary text not null,
  required_flags jsonb not null,
  status varchar(32) not null
);

create index if not exists idx_paired_devices_user_id on paired_devices (user_id);
create unique index if not exists idx_paired_devices_connector_token on paired_devices (connector_token);
create index if not exists idx_pairing_challenges_user_id on pairing_challenges (user_id);
create unique index if not exists idx_pairing_challenges_pairing_code on pairing_challenges (pairing_code);
create index if not exists idx_command_requests_user_id on command_requests (user_id);
create index if not exists idx_command_requests_status_device on command_requests (status, device_id);
create index if not exists idx_approval_records_user_id on approval_records (user_id);

create table users (
  id uuid primary key,
  email text,
  password_hash text,
  phone text
);

create table reset_tokens (
  token text primary key,
  user_id uuid,
  created_at timestamptz
);

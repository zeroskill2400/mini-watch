CREATE TABLE IF NOT EXISTS public.messages (
    id bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    content text NOT NULL CHECK (char_length(content) BETWEEN 1 AND 200),
    created_at timestamptz NOT NULL DEFAULT now()
);

ALTER TABLE public.messages ENABLE ROW LEVEL SECURITY;

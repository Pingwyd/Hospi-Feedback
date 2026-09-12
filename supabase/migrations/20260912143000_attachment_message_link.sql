-- Link follow-up chat photos to messages; keep submission-time photos report-scoped (message_id NULL).

ALTER TABLE public.attachments
  ADD COLUMN message_id UUID NULL REFERENCES public.messages (id) ON DELETE CASCADE;

CREATE INDEX attachments_message_id_idx ON public.attachments (message_id)
  WHERE message_id IS NOT NULL;

-- Atomic reporter follow-up: one message row and one attachment row in a single transaction.
CREATE OR REPLACE FUNCTION public.create_reporter_followup_attachment(
  p_report_id UUID,
  p_content TEXT,
  p_storage_path TEXT,
  p_file_type TEXT
)
RETURNS TABLE (
  message_id UUID,
  attachment_id UUID,
  message_created_at TIMESTAMPTZ,
  attachment_uploaded_at TIMESTAMPTZ,
  file_type TEXT
)
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = public
AS $$
DECLARE
  v_message_id UUID;
  v_message_created_at TIMESTAMPTZ;
  v_attachment_id UUID;
  v_attachment_uploaded_at TIMESTAMPTZ;
BEGIN
  INSERT INTO public.messages (report_id, sender_type, content)
  VALUES (p_report_id, 'reporter', p_content)
  RETURNING id, created_at INTO v_message_id, v_message_created_at;

  INSERT INTO public.attachments (report_id, message_id, storage_path, file_type)
  VALUES (p_report_id, v_message_id, p_storage_path, p_file_type)
  RETURNING id, uploaded_at INTO v_attachment_id, v_attachment_uploaded_at;

  RETURN QUERY
  SELECT
    v_message_id,
    v_attachment_id,
    v_message_created_at,
    v_attachment_uploaded_at,
    p_file_type;
END;
$$;

COMMENT ON FUNCTION public.create_reporter_followup_attachment IS
  'Inserts a reporter message and linked attachment atomically for follow-up photo uploads.';

-- Callable only via FastAPI service_role PostgREST client, not anon/authenticated keys.
REVOKE ALL ON FUNCTION public.create_reporter_followup_attachment(
  UUID, TEXT, TEXT, TEXT
) FROM PUBLIC, anon, authenticated;

GRANT EXECUTE ON FUNCTION public.create_reporter_followup_attachment(
  UUID, TEXT, TEXT, TEXT
) TO service_role;

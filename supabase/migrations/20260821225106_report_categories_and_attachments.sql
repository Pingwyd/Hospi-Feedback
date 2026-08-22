-- Multi-select categories and image attachments for a report.
-- storage_path is a Supabase Storage object path. EXIF strip happens in the app before save.

CREATE TABLE public.report_categories (
  report_id UUID NOT NULL REFERENCES public.reports (id) ON DELETE CASCADE,
  category_id UUID NOT NULL REFERENCES public.categories (id) ON DELETE RESTRICT,
  PRIMARY KEY (report_id, category_id)
);

CREATE TABLE public.attachments (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  report_id UUID REFERENCES public.reports (id) ON DELETE CASCADE,
  storage_path TEXT NOT NULL,
  file_type TEXT,
  uploaded_at TIMESTAMPTZ DEFAULT now()
);

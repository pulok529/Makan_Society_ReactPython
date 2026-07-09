import { apiRequest } from "./client";

export type BackgroundJob = {
  id: number;
  job_type: string;
  status: string;
  created_by: number | null;
  payload_json: string | null;
  result_summary: string | null;
  result_path: string | null;
  output_filename: string | null;
  output_content_type: string | null;
  progress_current: number;
  progress_total: number;
  created_at: string;
  updated_at: string;
};

export function createReportExportJob(accessToken: string, params: URLSearchParams) {
  return apiRequest<BackgroundJob>(`/api/jobs/report-export?${params.toString()}`, accessToken, {
    method: "POST",
  });
}

export function createBulkSmsJob(accessToken: string, payload: { member_ids: number[]; template_id: number | null; message_body: string | null }) {
  return apiRequest<BackgroundJob>("/api/jobs/bulk-sms", accessToken, {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

import { useQuery } from "@tanstack/react-query";

import { apiRequest } from "../api/client";
import { BackgroundJob } from "../api/jobs";

export function useJobStatus(jobId: number | null, accessToken: string | null, enabled = true) {
  return useQuery({
    queryKey: ["background-job", jobId],
    enabled: enabled && !!accessToken && !!jobId,
    queryFn: () => apiRequest<BackgroundJob>(`/api/jobs/${jobId}`, accessToken!),
    refetchInterval: (query) => {
      const status = (query.state.data as BackgroundJob | undefined)?.status;
      return status === "pending" || status === "running" ? 2000 : false;
    },
  });
}

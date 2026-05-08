const apiBaseUrl = import.meta.env.VITE_API_BASE_URL ?? "http://localhost:8000";

export type SmsSendResult = {
  success: boolean;
  provider_code: string | null;
  provider_message: string;
  raw_response: string | Record<string, unknown>;
  recipients: string[];
  dry_run: boolean;
};

export type SmsBalanceResult = {
  success: boolean;
  provider_code: string | null;
  provider_message: string;
  raw_response: string | Record<string, unknown>;
  balance: string | null;
  dry_run: boolean;
};

async function smsRequest<T>(path: string, accessToken: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${apiBaseUrl}${path}`, {
    ...init,
    headers: {
      "Content-Type": "application/json",
      Authorization: `Bearer ${accessToken}`,
      ...(init?.headers ?? {}),
    },
  });

  if (!response.ok) {
    const payload = await response.json().catch(() => null);
    throw new Error(payload?.detail ?? "SMS request failed");
  }

  return response.json() as Promise<T>;
}

export function sendTestSms(accessToken: string, number: string, message: string) {
  return smsRequest<SmsSendResult>("/api/sms/send", accessToken, {
    method: "POST",
    body: JSON.stringify({ number, message }),
  });
}

export function getSmsBalance(accessToken: string) {
  return smsRequest<SmsBalanceResult>("/api/sms/balance", accessToken);
}

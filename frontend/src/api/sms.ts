import { apiRequest } from "../shared/api/client";

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

export function sendTestSms(accessToken: string, number: string, message: string) {
  return apiRequest<SmsSendResult>("/api/sms/send", accessToken, {
    method: "POST",
    body: JSON.stringify({ number, message }),
  });
}

export function getSmsBalance(accessToken: string) {
  return apiRequest<SmsBalanceResult>("/api/sms/balance", accessToken);
}

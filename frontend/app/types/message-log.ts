export interface MessageLog {
  id: number;
  phone_number: string | null;
  message_type: string;
  direction: string;
  text: string | null;
  processed: boolean;
  blocked: boolean;
  created_at: string;
}

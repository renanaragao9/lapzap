export interface Business {
  id: number;
  user_id: number | null;
  name: string;
  business_type: string;
  contact_phone_number: string;
  plan: string;
  status: "pending_setup" | "active";
  visibility: "public" | "private";
  evolution_instance_name: string | null;
  created_at: string;
}

export type IntegrationType = "google_calendar" | "outlook_calendar" | "generic";

export interface BusinessIntegration {
  id: number;
  business_id: number;
  name: string;
  type: IntegrationType;
  host: string | null;
  email: string | null;
  has_secret: boolean;
  created_at: string;
  updated_at: string;
}

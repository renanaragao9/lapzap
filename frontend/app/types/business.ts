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

export interface Business {
  id: number;
  name: string;
  business_type: string;
  contact_phone_number: string;
  plan: string;
  status: "pending_setup" | "active";
  evolution_instance_name: string | null;
  created_at: string;
}

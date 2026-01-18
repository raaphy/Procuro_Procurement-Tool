export interface OrderLine {
  id?: number;
  description: string;
  unit_price: number;
  quantity: number;
  unit: string;
  stated_total_price: number | null;
  calculated_total_price?: number;
  has_price_mismatch?: boolean;
}

export interface StatusHistory {
  id: number;
  from_status: string | null;
  to_status: string;
  changed_at: string;
  changed_by: string;
}

export interface ProcurementRequest {
  id: number;
  requestor_name: string;
  title: string;
  vendor_name: string;
  vat_id: string;
  department: string;
  commodity_group_id: string;
  currency: string;
  stated_total_cost: number | null;
  calculated_total_cost: number;
  has_total_mismatch: boolean;
  status: 'Open' | 'In Progress' | 'Closed';
  order_lines: OrderLine[];
  status_history: StatusHistory[];
  pdf_filename: string | null;
  created_at: string;
  updated_at: string;
}

export interface CommodityGroup {
  id: string;
  category: string;
  name: string;
}

export interface PdfExtractionResult {
  vendor_name: string | null;
  vat_id: string | null;
  department: string | null;
  requestor_name: string | null;
  title: string | null;
  currency: string | null;
  stated_total_cost: number | null;
  order_lines: OrderLine[];
}

export interface CreateRequestPayload {
  requestor_name: string;
  title: string;
  vendor_name: string;
  vat_id: string;
  department: string;
  commodity_group_id: string;
  currency: string;
  stated_total_cost: number | null;
  order_lines: Omit<OrderLine, 'id'>[];
}

export interface UpdateRequestPayload extends Partial<CreateRequestPayload> {}

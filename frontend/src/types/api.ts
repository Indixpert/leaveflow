export interface User {
  id: number;
  username: string;
  first_name: string;
  last_name: string;
  email: string;
}

export interface LeaveType {
  id: number;
  name: string;
  max_days_per_year: number;
  requires_document: boolean;
  carry_forward_limit: number;
}

export type LeaveRequestStatus =
  | 'draft'
  | 'pending_manager'
  | 'pending_hr'
  | 'approved'
  | 'rejected'
  | 'cancelled';

export interface ApprovalStep {
  approver: string;
  role: 'manager' | 'hr';
  decision: 'pending' | 'approved' | 'rejected';
  comment: string;
  decided_at: string | null;
}

export interface LeaveRequest {
  id: string; // UUID
  employee: User;
  leave_type: string;
  start_date: string; // YYYY-MM-DD
  end_date: string; // YYYY-MM-DD
  total_days: number;
  reason: string;
  document: string | null;
  status: LeaveRequestStatus;
  created_at: string; // ISO 8601
  updated_at: string; // ISO 8601
  approval_steps: ApprovalStep[];
}

export interface LeaveRequestCreatePayload {
  leave_type_id: number;
  start_date: string;
  end_date: string;
  reason?: string;
  document?: File;
}

export interface User {
  id: number;
  username: string;
  email: string;
  first_name: string;
  last_name: string;
}

export interface LeaveType {
  id: number;
  name: string;
  max_days_per_year: number;
  requires_document: boolean;
  carry_forward_limit: number;
}

export interface PublicHoliday {
  id: number;
  name: string;
  date: string; // YYYY-MM-DD
}

export type LeaveRequestStatus = 'draft' | 'pending_manager' | 'pending_hr' | 'approved' | 'rejected' | 'cancelled';
export type LeaveRequestStatusDisplay = 'Draft' | 'Pending Manager Approval' | 'Pending HR Approval' | 'Approved' | 'Rejected' | 'Cancelled';

export interface ApprovalStep {
  id: number;
  approver: User;
  role: 'manager' | 'hr';
  decision: 'pending' | 'approved' | 'rejected';
  comment: string;
  decided_at: string | null;
}

export interface LeaveRequest {
  id: string; // UUID
  employee: User;
  leave_type: LeaveType;
  start_date: string; // YYYY-MM-DD
  end_date: string; // YYYY-MM-DD
  total_days: number;
  reason: string;
  document: string | null; // URL to the document
  status: LeaveRequestStatus;
  status_display: LeaveRequestStatusDisplay;
  approval_steps: ApprovalStep[];
  created_at: string;
  updated_at: string;
}

export interface LeaveRequestCreatePayload {
  leave_type: number;
  start_date: string; // YYYY-MM-DD
  end_date: string; // YYYY-MM-DD
  reason: string;
  document?: File;
}

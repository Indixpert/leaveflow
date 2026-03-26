import axios from './axiosConfig';
import { LeaveType, LeaveRequest, LeaveRequestCreatePayload } from '../types/api';

export const getLeaveTypes = async (): Promise<LeaveType[]> => {
  const response = await axios.get<LeaveType[]>('/leaves/types/');
  return response.data;
};

export const getLeaveRequests = async (): Promise<LeaveRequest[]> => {
  const response = await axios.get<LeaveRequest[]>('/leaves/requests/');
  return response.data;
};

export interface LeaveBalance {
    balance: number;
    allowance: number;
    carry_forward: number;
    taken: number;
}

export const getLeaveBalance = async (leaveTypeId: number): Promise<LeaveBalance> => {
    const response = await axios.get<LeaveBalance>(`/leaves/types/${leaveTypeId}/balance/`);
    return response.data;
};

export const calculateLeaveDays = async (startDate: string, endDate: string): Promise<{ total_days: number }> => {
    const response = await axios.get<{ total_days: number }>(`/leaves/requests/calculate_days/`, {
        params: {
            start_date: startDate,
            end_date: endDate,
        }
    });
    return response.data;
};

export const createLeaveRequest = async (payload: LeaveRequestCreatePayload): Promise<LeaveRequest> => {
  const formData = new FormData();
  formData.append('leave_type_id', payload.leave_type_id.toString());
  formData.append('start_date', payload.start_date);
  formData.append('end_date', payload.end_date);
  if (payload.reason) {
    formData.append('reason', payload.reason);
  }
  if (payload.document) {
    formData.append('document', payload.document);
  }

  const response = await axios.post<LeaveRequest>('/leaves/requests/', formData, {
    headers: {
      'Content-Type': 'multipart/form-data',
    },
  });
  return response.data;
};

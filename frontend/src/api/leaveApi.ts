import axios from './axiosConfig';
import { LeaveType, LeaveRequest, LeaveRequestCreatePayload } from '../types/api';

export const getLeaveTypes = async (): Promise<LeaveType[]> => {
  const response = await axios.get<LeaveType[]>('/leaves/types/');
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

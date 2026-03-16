import { axiosInstance } from './axiosConfig';
import { LeaveRequest, LeaveType, LeaveRequestCreatePayload } from '../types/api';

export const getLeaveRequests = async (): Promise<LeaveRequest[]> => {
  const response = await axiosInstance.get('/leaves/leave-requests/');
  return response.data;
};

export const getLeaveTypes = async (): Promise<LeaveType[]> => {
  const response = await axiosInstance.get('/leaves/leave-types/');
  return response.data;
};

export const createLeaveRequest = async (payload: LeaveRequestCreatePayload): Promise<LeaveRequest> => {
  const formData = new FormData();
  formData.append('leave_type', payload.leave_type.toString());
  formData.append('start_date', payload.start_date);
  formData.append('end_date', payload.end_date);
  formData.append('reason', payload.reason);
  if (payload.document) {
    formData.append('document', payload.document);
  }

  const response = await axiosInstance.post('/leaves/leave-requests/', formData, {
    headers: {
      'Content-Type': 'multipart/form-data',
    },
  });
  return response.data;
};

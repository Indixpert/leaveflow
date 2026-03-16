import React, { useState } from 'react';
import { useForm, SubmitHandler } from 'react-hook-form';
import { useMutation, useQuery, useQueryClient } from 'react-query';
import { createLeaveRequest, getLeaveTypes } from '../../api/leaveApi';
import { LeaveRequestCreatePayload, LeaveType } from '../../types/api';

interface FormValues {
  leave_type: number;
  start_date: string;
  end_date: string;
  reason: string;
  document?: FileList;
}

interface LeaveRequestFormProps {
  onSuccess?: () => void;
}

export const LeaveRequestForm: React.FC<LeaveRequestFormProps> = ({ onSuccess }) => {
  const queryClient = useQueryClient();
  const { register, handleSubmit, formState: { errors }, watch, reset } = useForm<FormValues>();
  const [serverError, setServerError] = useState<string | null>(null);

  const { data: leaveTypes, isLoading: isLoadingLeaveTypes } = useQuery<LeaveType[]>('leaveTypes', getLeaveTypes);

  const mutation = useMutation(createLeaveRequest, {
    onSuccess: () => {
      queryClient.invalidateQueries('leaveRequests');
      reset();
      if (onSuccess) onSuccess();
      alert('Leave request submitted successfully!');
    },
    onError: (error: any) => {
      const errorData = error.response?.data;
      if (typeof errorData === 'object' && errorData !== null) {
        const messages = Object.entries(errorData).map(([key, value]) => `${key}: ${Array.isArray(value) ? value.join(', ') : value}`);
        setServerError(messages.join('; '));
      } else {
        setServerError(errorData || 'An unexpected error occurred.');
      }
    },
  });

  const onSubmit: SubmitHandler<FormValues> = data => {
    setServerError(null);
    const payload: LeaveRequestCreatePayload = {
      ...data,
      leave_type: Number(data.leave_type),
      document: data.document && data.document.length > 0 ? data.document[0] : undefined,
    };
    mutation.mutate(payload);
  };

  const selectedLeaveTypeId = watch('leave_type');
  const selectedLeaveType = leaveTypes?.find(lt => lt.id === Number(selectedLeaveTypeId));

  return (
    <form onSubmit={handleSubmit(onSubmit)} className="space-y-6 bg-white p-8 rounded-lg shadow-md">
      <h2 className="text-2xl font-bold text-gray-800">New Leave Request</h2>
      
      {serverError && <div className="p-3 bg-red-100 text-red-700 rounded text-sm">{serverError}</div>}

      <div>
        <label htmlFor="leave_type" className="block text-sm font-medium text-gray-700">Leave Type</label>
        <select
          id="leave_type"
          {...register('leave_type', { required: 'Leave type is required' })}
          className="mt-1 block w-full p-2 border border-gray-300 rounded-md shadow-sm focus:ring-indigo-500 focus:border-indigo-500"
          disabled={isLoadingLeaveTypes}
        >
          <option value="">{isLoadingLeaveTypes ? 'Loading...' : 'Select a leave type'}</option>
          {leaveTypes?.map(type => (
            <option key={type.id} value={type.id}>{type.name}</option>
          ))}
        </select>
        {errors.leave_type && <p className="mt-1 text-sm text-red-600">{errors.leave_type.message}</p>}
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <div>
          <label htmlFor="start_date" className="block text-sm font-medium text-gray-700">Start Date</label>
          <input type="date" id="start_date" {...register('start_date', { required: 'Start date is required' })} className="mt-1 block w-full p-2 border border-gray-300 rounded-md shadow-sm" />
          {errors.start_date && <p className="mt-1 text-sm text-red-600">{errors.start_date.message}</p>}
        </div>
        <div>
          <label htmlFor="end_date" className="block text-sm font-medium text-gray-700">End Date</label>
          <input type="date" id="end_date" {...register('end_date', { required: 'End date is required' })} className="mt-1 block w-full p-2 border border-gray-300 rounded-md shadow-sm" />
          {errors.end_date && <p className="mt-1 text-sm text-red-600">{errors.end_date.message}</p>}
        </div>
      </div>

      <div>
        <label htmlFor="reason" className="block text-sm font-medium text-gray-700">Reason</label>
        <textarea id="reason" rows={4} {...register('reason', { required: 'Reason is required' })} className="mt-1 block w-full p-2 border border-gray-300 rounded-md shadow-sm" />
        {errors.reason && <p className="mt-1 text-sm text-red-600">{errors.reason.message}</p>}
      </div>

      {selectedLeaveType?.requires_document && (
        <div>
          <label htmlFor="document" className="block text-sm font-medium text-gray-700">Supporting Document (Required)</label>
          <input type="file" id="document" {...register('document', { required: `Document is required for ${selectedLeaveType.name}` })} className="mt-1 block w-full text-sm text-gray-500 file:mr-4 file:py-2 file:px-4 file:rounded-full file:border-0 file:text-sm file:font-semibold file:bg-indigo-50 file:text-indigo-700 hover:file:bg-indigo-100" />
          {errors.document && <p className="mt-1 text-sm text-red-600">{errors.document.message}</p>}
        </div>
      )}

      <div>
        <button type="submit" disabled={mutation.isLoading} className="w-full flex justify-center py-2 px-4 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-indigo-600 hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500 disabled:bg-indigo-400 disabled:cursor-not-allowed">
          {mutation.isLoading ? 'Submitting...' : 'Submit Request'}
        </button>
      </div>
    </form>
  );
};

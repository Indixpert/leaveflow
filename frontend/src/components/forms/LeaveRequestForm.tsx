import React, { useState } from 'react';
import { useForm, SubmitHandler } from 'react-hook-form';
import { useQuery, useMutation } from '@tanstack/react-query';
import { getLeaveTypes, createLeaveRequest } from '../../api/leaveApi';
import { LeaveRequestCreatePayload } from '../../types/api';

interface LeaveRequestFormProps {
  onSuccess: () => void;
}

type FormValues = {
  leave_type_id: string;
  start_date: string;
  end_date: string;
  reason: string;
  document?: FileList;
};

export const LeaveRequestForm: React.FC<LeaveRequestFormProps> = ({ onSuccess }) => {
  const [serverError, setServerError] = useState<string | null>(null);
  const {
    register,
    handleSubmit,
    formState: { errors, isSubmitting },
    watch,
  } = useForm<FormValues>();

  const { data: leaveTypes, isLoading: isLoadingLeaveTypes } = useQuery({
    queryKey: ['leaveTypes'],
    queryFn: getLeaveTypes,
  });

  const createLeaveMutation = useMutation({
    mutationFn: createLeaveRequest,
    onSuccess: () => {
      onSuccess();
    },
    onError: (error: any) => {
      const message = error.response?.data?.detail || 'An unexpected error occurred.';
      setServerError(message);
    },
  });

  const onSubmit: SubmitHandler<FormValues> = (data) => {
    setServerError(null);
    const payload: LeaveRequestCreatePayload = {
      leave_type_id: parseInt(data.leave_type_id, 10),
      start_date: data.start_date,
      end_date: data.end_date,
      reason: data.reason,
      document: data.document?.[0],
    };
    createLeaveMutation.mutate(payload);
  };

  const selectedLeaveTypeId = watch('leave_type_id');
  const selectedLeaveType = leaveTypes?.find(lt => lt.id === parseInt(selectedLeaveTypeId, 10));
  const requiresDocument = selectedLeaveType?.requires_document || false;

  return (
    <form onSubmit={handleSubmit(onSubmit)} className="space-y-6 bg-white p-8 shadow-md rounded-lg">
      <h2 className="text-2xl font-bold text-gray-800">New Leave Request</h2>

      {createLeaveMutation.isSuccess && (
        <div className="p-4 mb-4 text-sm text-green-700 bg-green-100 rounded-lg" role="alert">
          Leave request submitted successfully!
        </div>
      )}

      {serverError && (
        <div className="p-4 mb-4 text-sm text-red-700 bg-red-100 rounded-lg" role="alert">
          {serverError}
        </div>
      )}

      <div>
        <label htmlFor="leave_type_id" className="block text-sm font-medium text-gray-700">
          Leave Type
        </label>
        <select
          id="leave_type_id"
          {...register('leave_type_id', { required: 'Leave type is required' })}
          className="mt-1 block w-full pl-3 pr-10 py-2 text-base border-gray-300 focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm rounded-md"
          disabled={isLoadingLeaveTypes || isSubmitting}
        >
          <option value="">{isLoadingLeaveTypes ? 'Loading...' : 'Select a leave type'}</option>
          {leaveTypes?.map((type) => (
            <option key={type.id} value={type.id}>
              {type.name}
            </option>
          ))}
        </select>
        {errors.leave_type_id && <p className="mt-2 text-sm text-red-600">{errors.leave_type_id.message}</p>}
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <div>
          <label htmlFor="start_date" className="block text-sm font-medium text-gray-700">
            Start Date
          </label>
          <input
            type="date"
            id="start_date"
            {...register('start_date', { required: 'Start date is required' })}
            className="mt-1 block w-full border-gray-300 rounded-md shadow-sm focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm"
            disabled={isSubmitting}
          />
          {errors.start_date && <p className="mt-2 text-sm text-red-600">{errors.start_date.message}</p>}
        </div>
        <div>
          <label htmlFor="end_date" className="block text-sm font-medium text-gray-700">
            End Date
          </label>
          <input
            type="date"
            id="end_date"
            {...register('end_date', { required: 'End date is required' })}
            className="mt-1 block w-full border-gray-300 rounded-md shadow-sm focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm"
            disabled={isSubmitting}
          />
          {errors.end_date && <p className="mt-2 text-sm text-red-600">{errors.end_date.message}</p>}
        </div>
      </div>

      <div>
        <label htmlFor="reason" className="block text-sm font-medium text-gray-700">
          Reason
        </label>
        <textarea
          id="reason"
          rows={4}
          {...register('reason', { required: 'Reason is required' })}
          className="mt-1 block w-full border border-gray-300 rounded-md shadow-sm focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm"
          disabled={isSubmitting}
        />
        {errors.reason && <p className="mt-2 text-sm text-red-600">{errors.reason.message}</p>}
      </div>

      <div>
        <label htmlFor="document" className="block text-sm font-medium text-gray-700">
          Supporting Document {requiresDocument && <span className="text-red-500">*</span>}
        </label>
        <input
          type="file"
          id="document"
          {...register('document', { required: requiresDocument ? 'Document is required for this leave type' : false })}
          className="mt-1 block w-full text-sm text-gray-900 border border-gray-300 rounded-lg cursor-pointer bg-gray-50 focus:outline-none"
          disabled={isSubmitting}
        />
        {errors.document && <p className="mt-2 text-sm text-red-600">{errors.document.message}</p>}
      </div>

      <div className="flex justify-end">
        <button
          type="submit"
          disabled={isSubmitting || createLeaveMutation.isSuccess}
          className="inline-flex justify-center py-2 px-4 border border-transparent shadow-sm text-sm font-medium rounded-md text-white bg-indigo-600 hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500 disabled:bg-indigo-300"
        >
          {isSubmitting ? 'Submitting...' : 'Submit Request'}
        </button>
      </div>
    </form>
  );
};

import React from 'react';
import { useNavigate } from 'react-router-dom';
import { LeaveRequestForm } from '../components/forms/LeaveRequestForm';

const NewLeaveRequest: React.FC = () => {
  const navigate = useNavigate();

  const handleSuccess = () => {
    // Navigate back to dashboard after a short delay to show success message
    setTimeout(() => {
      navigate('/');
    }, 1500);
  };

  return (
    <div className="container mx-auto p-4 sm:p-6 lg:p-8">
      <div className="max-w-2xl mx-auto">
        <LeaveRequestForm onSuccess={handleSuccess} />
      </div>
    </div>
  );
};

export default NewLeaveRequest;

import { useQuery } from '@tanstack/react-query';
import { Clock, CheckCircle, XCircle, Loader } from 'lucide-react';
import { fetchRuns } from '../lib/api';
import { format } from 'date-fns';

export default function Scans() {
  const { data: runs, isLoading } = useQuery({
    queryKey: ['runs'],
    queryFn: fetchRuns,
    refetchInterval: 5000, // Auto-refresh
  });

  const getStatusIcon = (status) => {
    switch (status) {
      case 'completed':
        return <CheckCircle className="w-5 h-5 text-green-600" />;
      case 'failed':
        return <XCircle className="w-5 h-5 text-red-600" />;
      case 'running':
        return <Loader className="w-5 h-5 text-blue-600 animate-spin" />;
      default:
        return <Clock className="w-5 h-5 text-gray-600" />;
    }
  };

  const getStatusColor = (status) => {
    switch (status) {
      case 'completed':
        return 'bg-green-100 text-green-800';
      case 'failed':
        return 'bg-red-100 text-red-800';
      case 'running':
        return 'bg-blue-100 text-blue-800';
      case 'queued':
        return 'bg-yellow-100 text-yellow-800';
      default:
        return 'bg-gray-100 text-gray-800';
    }
  };

  if (isLoading) return <div className="p-8">Loading...</div>;

  return (
    <div className="p-8">
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-gray-900">Pentest Scans</h1>
        <p className="text-gray-600 mt-2">View all pentest scan runs</p>
      </div>

      <div className="bg-white rounded-lg shadow overflow-hidden">
        <table className="min-w-full divide-y divide-gray-200">
          <thead className="bg-gray-50">
            <tr>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">ID</th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Target ID</th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Status</th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Started</th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Completed</th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Error</th>
            </tr>
          </thead>
          <tbody className="bg-white divide-y divide-gray-200">
            {runs?.map((run) => (
              <tr key={run.id}>
                <td className="px-6 py-4 whitespace-nowrap font-medium text-gray-900">#{run.id}</td>
                <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-600">{run.target_id}</td>
                <td className="px-6 py-4 whitespace-nowrap">
                  <div className="flex items-center gap-2">
                    {getStatusIcon(run.status)}
                    <span className={`px-2 py-1 text-xs font-medium rounded-full ${getStatusColor(run.status)}`}>
                      {run.status}
                    </span>
                  </div>
                </td>
                <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-600">
                  {run.started_at ? format(new Date(run.started_at), 'MMM d, HH:mm') : '-'}
                </td>
                <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-600">
                  {run.completed_at ? format(new Date(run.completed_at), 'MMM d, HH:mm') : '-'}
                </td>
                <td className="px-6 py-4 text-sm text-red-600">
                  {run.error_message ? run.error_message.substring(0, 50) + '...' : '-'}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}

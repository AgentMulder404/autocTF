import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { Clock, CheckCircle, XCircle, Loader, FileText, X, Download, Trash2 } from 'lucide-react';
import { fetchRuns, fetchRunSummary, deleteRun } from '../lib/api';
import { format } from 'date-fns';

export default function Scans() {
  const queryClient = useQueryClient();
  const [selectedRun, setSelectedRun] = useState(null);
  const [showSummary, setShowSummary] = useState(false);
  const [summary, setSummary] = useState(null);
  const [loadingSummary, setLoadingSummary] = useState(false);

  const { data: runs, isLoading } = useQuery({
    queryKey: ['runs'],
    queryFn: fetchRuns,
    refetchInterval: 5000, // Auto-refresh
  });

  const deleteMutation = useMutation({
    mutationFn: deleteRun,
    onSuccess: () => {
      queryClient.invalidateQueries(['runs']);
      queryClient.invalidateQueries(['targets']);
    },
  });

  const handleViewSummary = async (run) => {
    setSelectedRun(run);
    setShowSummary(true);
    setLoadingSummary(true);
    try {
      const summaryData = await fetchRunSummary(run.id);
      setSummary(summaryData);
    } catch (error) {
      alert('Failed to load summary: ' + error.message);
      setShowSummary(false);
    } finally {
      setLoadingSummary(false);
    }
  };

  const handleDownloadSummary = () => {
    if (!summary) return;
    const blob = new Blob([summary.summary], { type: 'text/markdown' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `pentest-summary-${selectedRun.id}.md`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  };

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
              <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase">Actions</th>
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
                <td className="px-6 py-4 whitespace-nowrap text-right text-sm font-medium">
                  <div className="flex items-center justify-end gap-3">
                    {run.status === 'completed' && (
                      <>
                        <button
                          onClick={() => handleViewSummary(run)}
                          className="inline-flex items-center gap-2 text-cyan-600 hover:text-cyan-900"
                        >
                          <FileText className="w-5 h-5" />
                          <span>View Summary</span>
                        </button>
                        <button
                          onClick={() => {
                            if (confirm('Delete this scan and all associated vulnerabilities?')) {
                              deleteMutation.mutate(run.id);
                            }
                          }}
                          className="text-red-600 hover:text-red-900"
                          title="Delete scan"
                        >
                          <Trash2 className="w-5 h-5" />
                        </button>
                      </>
                    )}
                  </div>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {/* Summary Modal */}
      {showSummary && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-lg shadow-xl max-w-4xl w-full max-h-[90vh] flex flex-col">
            {/* Header */}
            <div className="flex items-center justify-between p-6 border-b">
              <h2 className="text-2xl font-bold text-gray-900">
                Pentest Summary Report #{selectedRun?.id}
              </h2>
              <div className="flex gap-2">
                <button
                  onClick={handleDownloadSummary}
                  className="p-2 text-gray-600 hover:text-gray-900 hover:bg-gray-100 rounded-lg"
                  title="Download as Markdown"
                >
                  <Download className="w-5 h-5" />
                </button>
                <button
                  onClick={() => setShowSummary(false)}
                  className="p-2 text-gray-600 hover:text-gray-900 hover:bg-gray-100 rounded-lg"
                >
                  <X className="w-5 h-5" />
                </button>
              </div>
            </div>

            {/* Content */}
            <div className="flex-1 overflow-y-auto p-6">
              {loadingSummary ? (
                <div className="flex items-center justify-center py-12">
                  <Loader className="w-8 h-8 text-cyan-600 animate-spin" />
                  <span className="ml-3 text-gray-600">Generating summary...</span>
                </div>
              ) : summary ? (
                <div className="prose max-w-none">
                  <pre className="whitespace-pre-wrap font-sans text-sm leading-relaxed text-gray-800">
                    {summary.summary}
                  </pre>
                </div>
              ) : (
                <div className="text-center py-12 text-gray-500">
                  Failed to load summary
                </div>
              )}
            </div>

            {/* Footer with Statistics */}
            {summary && !loadingSummary && (
              <div className="p-6 border-t bg-gray-50">
                <div className="grid grid-cols-6 gap-4">
                  <div className="text-center">
                    <div className="text-2xl font-bold text-gray-900">{summary.statistics.total_vulnerabilities}</div>
                    <div className="text-xs text-gray-600">Total</div>
                  </div>
                  <div className="text-center">
                    <div className="text-2xl font-bold text-red-600">{summary.statistics.critical}</div>
                    <div className="text-xs text-gray-600">Critical</div>
                  </div>
                  <div className="text-center">
                    <div className="text-2xl font-bold text-orange-600">{summary.statistics.high}</div>
                    <div className="text-xs text-gray-600">High</div>
                  </div>
                  <div className="text-center">
                    <div className="text-2xl font-bold text-yellow-600">{summary.statistics.medium}</div>
                    <div className="text-xs text-gray-600">Medium</div>
                  </div>
                  <div className="text-center">
                    <div className="text-2xl font-bold text-blue-600">{summary.statistics.low}</div>
                    <div className="text-xs text-gray-600">Low</div>
                  </div>
                  <div className="text-center">
                    <div className="text-2xl font-bold text-gray-900">{summary.statistics.duration}</div>
                    <div className="text-xs text-gray-600">Duration</div>
                  </div>
                </div>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
}

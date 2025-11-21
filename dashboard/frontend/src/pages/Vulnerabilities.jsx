import { useQuery } from '@tanstack/react-query';
import { AlertTriangle, Shield, CheckCircle } from 'lucide-react';
import { fetchVulnerabilities } from '../lib/api';
import { format } from 'date-fns';

export default function Vulnerabilities() {
  const { data: vulns, isLoading } = useQuery({
    queryKey: ['vulnerabilities'],
    queryFn: fetchVulnerabilities,
  });

  const getSeverityColor = (severity) => {
    switch (severity) {
      case 'critical':
        return 'bg-red-100 text-red-800 border-red-300';
      case 'high':
        return 'bg-orange-100 text-orange-800 border-orange-300';
      case 'medium':
        return 'bg-yellow-100 text-yellow-800 border-yellow-300';
      case 'low':
        return 'bg-blue-100 text-blue-800 border-blue-300';
      default:
        return 'bg-gray-100 text-gray-800 border-gray-300';
    }
  };

  if (isLoading) return <div className="p-8">Loading...</div>;

  return (
    <div className="p-8">
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-gray-900">Vulnerabilities</h1>
        <p className="text-gray-600 mt-2">All discovered security vulnerabilities</p>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
        <div className="bg-white rounded-lg shadow p-6">
          <div className="flex items-center gap-3">
            <AlertTriangle className="w-8 h-8 text-red-600" />
            <div>
              <p className="text-sm text-gray-600">Total Vulnerabilities</p>
              <p className="text-2xl font-bold">{vulns?.length || 0}</p>
            </div>
          </div>
        </div>
        <div className="bg-white rounded-lg shadow p-6">
          <div className="flex items-center gap-3">
            <Shield className="w-8 h-8 text-green-600" />
            <div>
              <p className="text-sm text-gray-600">Patched</p>
              <p className="text-2xl font-bold">{vulns?.filter(v => v.patched).length || 0}</p>
            </div>
          </div>
        </div>
        <div className="bg-white rounded-lg shadow p-6">
          <div className="flex items-center gap-3">
            <CheckCircle className="w-8 h-8 text-blue-600" />
            <div>
              <p className="text-sm text-gray-600">Exploited</p>
              <p className="text-2xl font-bold">{vulns?.filter(v => v.exploited).length || 0}</p>
            </div>
          </div>
        </div>
      </div>

      {/* Vulnerabilities List */}
      <div className="space-y-4">
        {vulns?.map((vuln) => (
          <div key={vuln.id} className="bg-white rounded-lg shadow p-6">
            <div className="flex items-start justify-between">
              <div className="flex-1">
                <div className="flex items-center gap-3 mb-2">
                  <h3 className="text-lg font-semibold text-gray-900">{vuln.type}</h3>
                  <span className={`px-3 py-1 text-xs font-bold rounded-full border ${getSeverityColor(vuln.severity)}`}>
                    {vuln.severity.toUpperCase()}
                  </span>
                  {vuln.exploited && (
                    <span className="px-3 py-1 text-xs font-medium rounded-full bg-red-100 text-red-800">
                      Exploited
                    </span>
                  )}
                  {vuln.patched && (
                    <span className="px-3 py-1 text-xs font-medium rounded-full bg-green-100 text-green-800">
                      Patched
                    </span>
                  )}
                </div>

                <div className="space-y-2 text-sm">
                  <p><span className="font-medium text-gray-700">Endpoint:</span> {vuln.endpoint}</p>
                  {vuln.param && <p><span className="font-medium text-gray-700">Parameter:</span> {vuln.param}</p>}
                  {vuln.description && (
                    <p><span className="font-medium text-gray-700">Description:</span> {vuln.description}</p>
                  )}
                  {vuln.proof_url && (
                    <p>
                      <span className="font-medium text-gray-700">Proof:</span>{' '}
                      <a href={vuln.proof_url} target="_blank" rel="noopener noreferrer" className="text-cyan-600 hover:underline">
                        View Screenshot
                      </a>
                    </p>
                  )}
                  <p className="text-gray-500">
                    Discovered: {format(new Date(vuln.created_at), 'MMM d, yyyy HH:mm')}
                  </p>
                </div>
              </div>
            </div>
          </div>
        ))}
      </div>

      {(!vulns || vulns.length === 0) && (
        <div className="bg-white rounded-lg shadow p-12 text-center">
          <Shield className="w-16 h-16 text-gray-400 mx-auto mb-4" />
          <h3 className="text-xl font-semibold text-gray-900 mb-2">No Vulnerabilities Found</h3>
          <p className="text-gray-600">Start a pentest scan to discover vulnerabilities</p>
        </div>
      )}
    </div>
  );
}

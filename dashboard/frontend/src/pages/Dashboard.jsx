import { useQuery } from '@tanstack/react-query';
import { Target, Activity, AlertTriangle, GitPullRequest, Shield, XCircle } from 'lucide-react';
import StatCard from '../components/StatCard';
import { fetchOverview, fetchTrends } from '../lib/api';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';

export default function Dashboard() {
  const { data: overview, isLoading } = useQuery({
    queryKey: ['overview'],
    queryFn: fetchOverview,
    refetchInterval: 5000, // Refresh every 5s
  });

  const { data: trends } = useQuery({
    queryKey: ['trends'],
    queryFn: () => fetchTrends(7), // Last 7 days
  });

  if (isLoading) {
    return (
      <div className="p-8">
        <div className="animate-pulse">Loading...</div>
      </div>
    );
  }

  return (
    <div className="p-8">
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-gray-900">Security Overview</h1>
        <p className="text-gray-600 mt-2">Real-time insights into your security posture</p>
      </div>

      {/* Stats Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
        <StatCard
          title="Total Targets"
          value={overview?.total_targets || 0}
          icon={Target}
          color="cyan"
        />
        <StatCard
          title="Active Scans"
          value={overview?.active_scans || 0}
          icon={Activity}
          color="orange"
        />
        <StatCard
          title="Total Vulnerabilities"
          value={overview?.total_vulnerabilities || 0}
          icon={AlertTriangle}
          color="red"
        />
        <StatCard
          title="Patched"
          value={overview?.patched_vulns || 0}
          icon={Shield}
          color="green"
        />
      </div>

      {/* Critical Stats */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
        <div className="bg-white rounded-lg shadow p-6">
          <div className="flex items-center gap-3">
            <div className="p-2 bg-red-100 rounded-lg">
              <XCircle className="w-5 h-5 text-red-600" />
            </div>
            <div>
              <p className="text-sm text-gray-600">Critical Vulnerabilities</p>
              <p className="text-2xl font-bold text-red-600">{overview?.critical_vulns || 0}</p>
            </div>
          </div>
        </div>

        <div className="bg-white rounded-lg shadow p-6">
          <div className="flex items-center gap-3">
            <div className="p-2 bg-orange-100 rounded-lg">
              <AlertTriangle className="w-5 h-5 text-orange-600" />
            </div>
            <div>
              <p className="text-sm text-gray-600">High Severity</p>
              <p className="text-2xl font-bold text-orange-600">{overview?.high_vulns || 0}</p>
            </div>
          </div>
        </div>

        <div className="bg-white rounded-lg shadow p-6">
          <div className="flex items-center gap-3">
            <div className="p-2 bg-blue-100 rounded-lg">
              <GitPullRequest className="w-5 h-5 text-blue-600" />
            </div>
            <div>
              <p className="text-sm text-gray-600">Open Pull Requests</p>
              <p className="text-2xl font-bold text-blue-600">{overview?.open_prs || 0}</p>
            </div>
          </div>
        </div>
      </div>

      {/* Trends Chart */}
      {trends && trends.length > 0 && (
        <div className="bg-white rounded-lg shadow p-6">
          <h2 className="text-xl font-semibold text-gray-900 mb-4">Vulnerability Trends (Last 7 Days)</h2>
          <ResponsiveContainer width="100%" height={300}>
            <LineChart data={trends}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="date" />
              <YAxis />
              <Tooltip />
              <Legend />
              <Line type="monotone" dataKey="vulnerabilities" stroke="#ef4444" name="Found" />
              <Line type="monotone" dataKey="patched" stroke="#10b981" name="Patched" />
            </LineChart>
          </ResponsiveContainer>
        </div>
      )}
    </div>
  );
}

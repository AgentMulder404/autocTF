import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { Plus, Play, Trash2, Github, AlertCircle } from 'lucide-react';
import { fetchTargets, createTarget, createTargetFromGitHub, deleteTarget, startScan } from '../lib/api';
import { format } from 'date-fns';

// GitHub URL validation
function validateGitHubURL(url) {
  if (!url || typeof url !== 'string') {
    return { valid: false, error: 'URL cannot be empty' };
  }

  const trimmed = url.trim();

  // Check for SSH format
  if (trimmed.startsWith('git@github.com:')) {
    const sshPattern = /^git@github\.com:([a-zA-Z0-9_-]+)\/([a-zA-Z0-9_.-]+?)(\.git)?$/;
    if (sshPattern.test(trimmed)) {
      return { valid: true };
    }
    return {
      valid: false,
      error: 'Invalid Git SSH URL. Expected format: git@github.com:owner/repo.git'
    };
  }

  // Check for HTTPS format
  try {
    const urlObj = new URL(trimmed);

    if (urlObj.hostname !== 'github.com') {
      return {
        valid: false,
        error: 'Not a GitHub URL. Please use a URL from github.com'
      };
    }

    const pathParts = urlObj.pathname.split('/').filter(p => p);

    if (pathParts.length < 2) {
      return {
        valid: false,
        error: 'Invalid GitHub URL. Must include owner and repository (e.g., https://github.com/owner/repo)'
      };
    }

    // Valid formats:
    // - /owner/repo
    // - /owner/repo.git
    // - /owner/repo/tree/branch

    return { valid: true };
  } catch (e) {
    return {
      valid: false,
      error: 'Invalid URL format. Expected: https://github.com/owner/repo'
    };
  }
}

export default function Targets() {
  const queryClient = useQueryClient();
  const [showForm, setShowForm] = useState(false);
  const [importMode, setImportMode] = useState('github'); // Default to GitHub for ease of use
  const [formData, setFormData] = useState({ name: '', url: '', ip_address: '' });
  const [githubUrl, setGithubUrl] = useState('');
  const [validationError, setValidationError] = useState('');

  const { data: targets, isLoading } = useQuery({
    queryKey: ['targets'],
    queryFn: fetchTargets,
  });

  const createMutation = useMutation({
    mutationFn: createTarget,
    onSuccess: () => {
      queryClient.invalidateQueries(['targets']);
      setShowForm(false);
      setFormData({ name: '', url: '', ip_address: '' });
    },
  });

  const createFromGitHubMutation = useMutation({
    mutationFn: createTargetFromGitHub,
    onSuccess: (data) => {
      console.log('[GitHub Import] Success:', data);
      queryClient.invalidateQueries(['targets']);
      setShowForm(false);
      setGithubUrl('');
      setValidationError('');
    },
    onError: (error) => {
      console.error('[GitHub Import] Error:', error);
      console.error('[GitHub Import] Error response:', error.response?.data);
    },
  });

  const deleteMutation = useMutation({
    mutationFn: deleteTarget,
    onSuccess: () => {
      queryClient.invalidateQueries(['targets']);
    },
  });

  const scanMutation = useMutation({
    mutationFn: startScan,
    onSuccess: () => {
      alert('Scan started!');
      queryClient.invalidateQueries(['runs']);
    },
  });

  const handleSubmit = (e) => {
    e.preventDefault();
    createMutation.mutate(formData);
  };

  const handleGitHubSubmit = (e) => {
    e.preventDefault();

    // Client-side validation
    console.log('[GitHub Import] Validating URL:', githubUrl);
    const validation = validateGitHubURL(githubUrl);

    if (!validation.valid) {
      console.error('[GitHub Import] Validation failed:', validation.error);
      setValidationError(validation.error);
      return;
    }

    console.log('[GitHub Import] Validation passed, submitting:', githubUrl);
    setValidationError('');
    createFromGitHubMutation.mutate(githubUrl);
  };

  // Get user-friendly error message
  const getErrorMessage = () => {
    const error = createFromGitHubMutation.error;

    if (!error) return null;

    // Check for response data first
    if (error.response?.data?.detail) {
      return error.response.data.detail;
    }

    // Check for network errors
    if (error.code === 'ERR_NETWORK' || error.message.includes('Network Error')) {
      return 'Cannot connect to AutoCTF API. Make sure the backend is running at http://localhost:8000';
    }

    // Check for status code errors
    if (error.response) {
      const status = error.response.status;
      if (status === 400) {
        return error.response.data?.detail || 'Invalid GitHub URL format';
      } else if (status === 409) {
        return error.response.data?.detail || 'Target already exists';
      } else if (status === 500) {
        return error.response.data?.detail || 'Server error while importing repository';
      }
    }

    // Fallback to generic error
    return error.message || 'Failed to import repository';
  };

  if (isLoading) return <div className="p-8">Loading...</div>;

  return (
    <div className="p-8">
      <div className="flex justify-between items-center mb-8">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">Targets</h1>
          <p className="text-gray-600 mt-2">Manage your pentest targets</p>
        </div>
        <button
          onClick={() => setShowForm(!showForm)}
          className="flex items-center gap-2 bg-cyan-600 text-white px-4 py-2 rounded-lg hover:bg-cyan-700"
        >
          <Plus className="w-5 h-5" />
          Add Target
        </button>
      </div>

      {/* Add Target Form */}
      {showForm && (
        <div className="bg-white rounded-lg shadow p-6 mb-6">
          <h2 className="text-xl font-semibold mb-4">Add New Target</h2>

          {/* Import Mode Toggle */}
          <div className="flex gap-2 mb-6 border-b">
            <button
              onClick={() => setImportMode('github')}
              className={`flex items-center gap-2 px-4 py-2 border-b-2 transition-colors ${
                importMode === 'github'
                  ? 'border-cyan-600 text-cyan-600'
                  : 'border-transparent text-gray-500 hover:text-gray-700'
              }`}
            >
              <Github className="w-5 h-5" />
              From GitHub
            </button>
            <button
              onClick={() => setImportMode('manual')}
              className={`px-4 py-2 border-b-2 transition-colors ${
                importMode === 'manual'
                  ? 'border-cyan-600 text-cyan-600'
                  : 'border-transparent text-gray-500 hover:text-gray-700'
              }`}
            >
              Manual Entry
            </button>
          </div>

          {/* GitHub URL Form */}
          {importMode === 'github' && (
            <form onSubmit={handleGitHubSubmit} className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  GitHub Repository URL
                </label>
                <input
                  type="text"
                  value={githubUrl}
                  onChange={(e) => {
                    setGithubUrl(e.target.value);
                    setValidationError(''); // Clear validation error on change
                  }}
                  className={`w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-cyan-500 focus:border-cyan-500 ${
                    validationError || createFromGitHubMutation.isError
                      ? 'border-red-300'
                      : 'border-gray-300'
                  }`}
                  placeholder="https://github.com/WebGoat/WebGoat"
                  required
                />
                <p className="text-sm text-gray-500 mt-1">
                  Examples: https://github.com/WebGoat/WebGoat, https://github.com/juice-shop/juice-shop
                </p>
              </div>

              {/* Client-side validation error */}
              {validationError && (
                <div className="p-3 bg-yellow-50 border border-yellow-200 rounded-lg flex items-start gap-2">
                  <AlertCircle className="w-5 h-5 text-yellow-600 flex-shrink-0 mt-0.5" />
                  <div className="text-yellow-800 text-sm">
                    <strong>Invalid URL:</strong> {validationError}
                  </div>
                </div>
              )}

              {/* Server-side error */}
              {createFromGitHubMutation.isError && !validationError && (
                <div className="p-3 bg-red-50 border border-red-200 rounded-lg flex items-start gap-2">
                  <AlertCircle className="w-5 h-5 text-red-600 flex-shrink-0 mt-0.5" />
                  <div className="text-red-800 text-sm">
                    <strong>Error:</strong> {getErrorMessage()}
                  </div>
                </div>
              )}

              <div className="flex gap-2">
                <button
                  type="submit"
                  disabled={createFromGitHubMutation.isPending}
                  className="bg-cyan-600 text-white px-4 py-2 rounded-lg hover:bg-cyan-700 disabled:opacity-50 flex items-center gap-2"
                >
                  <Github className="w-4 h-4" />
                  {createFromGitHubMutation.isPending ? 'Importing...' : 'Import from GitHub'}
                </button>
                <button
                  type="button"
                  onClick={() => {
                    setShowForm(false);
                    setValidationError('');
                    setGithubUrl('');
                  }}
                  className="bg-gray-200 text-gray-700 px-4 py-2 rounded-lg hover:bg-gray-300"
                >
                  Cancel
                </button>
              </div>
            </form>
          )}

          {/* Manual Entry Form */}
          {importMode === 'manual' && (
            <form onSubmit={handleSubmit} className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Name</label>
                <input
                  type="text"
                  value={formData.name}
                  onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-cyan-500 focus:border-cyan-500"
                  required
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">URL</label>
                <input
                  type="url"
                  value={formData.url}
                  onChange={(e) => setFormData({ ...formData, url: e.target.value })}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-cyan-500 focus:border-cyan-500"
                  placeholder="http://example.com"
                  required
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">IP Address (optional)</label>
                <input
                  type="text"
                  value={formData.ip_address}
                  onChange={(e) => setFormData({ ...formData, ip_address: e.target.value })}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-cyan-500 focus:border-cyan-500"
                  placeholder="192.168.1.1"
                />
              </div>
              <div className="flex gap-2">
                <button
                  type="submit"
                  disabled={createMutation.isPending}
                  className="bg-cyan-600 text-white px-4 py-2 rounded-lg hover:bg-cyan-700 disabled:opacity-50"
                >
                  {createMutation.isPending ? 'Adding...' : 'Add Target'}
                </button>
                <button
                  type="button"
                  onClick={() => setShowForm(false)}
                  className="bg-gray-200 text-gray-700 px-4 py-2 rounded-lg hover:bg-gray-300"
                >
                  Cancel
                </button>
              </div>
            </form>
          )}
        </div>
      )}

      {/* Targets List */}
      <div className="bg-white rounded-lg shadow overflow-hidden">
        <table className="min-w-full divide-y divide-gray-200">
          <thead className="bg-gray-50">
            <tr>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Name</th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">URL</th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">GitHub Repo</th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Status</th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Last Scan</th>
              <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase">Actions</th>
            </tr>
          </thead>
          <tbody className="bg-white divide-y divide-gray-200">
            {targets?.map((target) => (
              <tr key={target.id}>
                <td className="px-6 py-4 whitespace-nowrap">
                  <div className="flex items-center gap-2">
                    {target.github_repo && <Github className="w-4 h-4 text-gray-400" />}
                    <span className="font-medium text-gray-900">{target.name}</span>
                  </div>
                </td>
                <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-600">{target.url}</td>
                <td className="px-6 py-4 whitespace-nowrap text-sm">
                  {target.github_repo ? (
                    <a
                      href={target.github_repo}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="text-cyan-600 hover:underline"
                    >
                      {target.repo_owner}/{target.repo_name}
                    </a>
                  ) : (
                    <span className="text-gray-400">-</span>
                  )}
                </td>
                <td className="px-6 py-4 whitespace-nowrap">
                  <span className={`px-2 py-1 text-xs font-medium rounded-full ${
                    target.status === 'active' ? 'bg-green-100 text-green-800' : 'bg-gray-100 text-gray-800'
                  }`}>
                    {target.status}
                  </span>
                </td>
                <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-600">
                  {target.last_scan ? format(new Date(target.last_scan), 'MMM d, yyyy HH:mm') : 'Never'}
                </td>
                <td className="px-6 py-4 whitespace-nowrap text-right text-sm font-medium">
                  <button
                    onClick={() => scanMutation.mutate(target.id)}
                    disabled={scanMutation.isPending || target.has_active_scan}
                    className={`mr-3 ${target.has_active_scan ? 'text-gray-400 cursor-not-allowed' : 'text-cyan-600 hover:text-cyan-900'}`}
                    title={target.has_active_scan ? 'Scan already running' : 'Start scan'}
                  >
                    <Play className="w-5 h-5" />
                  </button>
                  {!target.has_active_scan && (
                    <button
                      onClick={() => {
                        if (confirm('Delete this target? This will also delete all associated scans and vulnerabilities.')) {
                          deleteMutation.mutate(target.id);
                        }
                      }}
                      className="text-red-600 hover:text-red-900"
                      title="Delete target"
                    >
                      <Trash2 className="w-5 h-5" />
                    </button>
                  )}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}

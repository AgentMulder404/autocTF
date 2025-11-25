import { useState, useEffect } from 'react';
import { Wifi, WifiOff, AlertCircle } from 'lucide-react';
import { checkHealth } from '../lib/api';

export default function ConnectionStatus() {
  const [status, setStatus] = useState('checking');
  const [health, setHealth] = useState(null);
  const [error, setError] = useState(null);

  useEffect(() => {
    const checkConnection = async () => {
      try {
        const healthData = await checkHealth();
        setHealth(healthData);
        setStatus(healthData.status === 'healthy' ? 'connected' : 'degraded');
        setError(null);
      } catch (err) {
        setStatus('disconnected');
        setError(err.message || 'Cannot connect to backend');
        setHealth(null);
      }
    };

    // Check immediately
    checkConnection();

    // Then check every 30 seconds
    const interval = setInterval(checkConnection, 30000);

    return () => clearInterval(interval);
  }, []);

  const getStatusIcon = () => {
    if (status === 'connected') {
      return <Wifi className="w-4 h-4 text-green-400" />;
    } else if (status === 'degraded') {
      return <AlertCircle className="w-4 h-4 text-yellow-400" />;
    } else if (status === 'disconnected') {
      return <WifiOff className="w-4 h-4 text-red-400" />;
    } else {
      return <Wifi className="w-4 h-4 text-gray-400 animate-pulse" />;
    }
  };

  const getStatusText = () => {
    if (status === 'connected') {
      return 'API Connected';
    } else if (status === 'degraded') {
      return 'API Degraded';
    } else if (status === 'disconnected') {
      return 'API Offline';
    } else {
      return 'Checking...';
    }
  };

  const getStatusColor = () => {
    if (status === 'connected') {
      return 'text-green-400';
    } else if (status === 'degraded') {
      return 'text-yellow-400';
    } else if (status === 'disconnected') {
      return 'text-red-400';
    } else {
      return 'text-gray-400';
    }
  };

  return (
    <div className="px-6 py-4 border-t border-gray-800">
      <div className="flex items-center gap-2">
        {getStatusIcon()}
        <div className="flex-1">
          <p className={`text-xs font-medium ${getStatusColor()}`}>
            {getStatusText()}
          </p>
          {health && (
            <p className="text-xs text-gray-500">
              DB: {health.database === 'connected' ? '✓' : '✗'}
              {' • '}
              Val: {health.validation.valid ? '✓' : '✗'}
            </p>
          )}
          {error && (
            <p className="text-xs text-red-400 mt-1">
              {error}
            </p>
          )}
        </div>
      </div>
    </div>
  );
}

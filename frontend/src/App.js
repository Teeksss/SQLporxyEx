import React, { useState, useEffect } from 'react';
import axios from 'axios';

function App() {
  const [status, setStatus] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    const checkBackend = async () => {
      try {
        setLoading(true);
        const response = await axios.get('/health', {
          timeout: 10000,
        });
        setStatus(response.data);
        setError(null);
      } catch (err) {
        console.error('Backend health check failed:', err);
        setError(err.message);
        setStatus({ 
          status: 'error', 
          message: 'Backend connection failed',
          details: err.message 
        });
      } finally {
        setLoading(false);
      }
    };

    checkBackend();
    
    // Check backend status every 30 seconds
    const interval = setInterval(checkBackend, 30000);
    
    return () => clearInterval(interval);
  }, []);

  const handleRefresh = () => {
    window.location.reload();
  };

  const handleAPITest = async () => {
    try {
      const response = await axios.get('/api/v1/info');
      alert(`API Test Successful!\n\nAPI Version: ${response.data.api_version}\nApp Version: ${response.data.app_version}\nCreator: ${response.data.creator}`);
    } catch (err) {
      alert(`API Test Failed!\n\nError: ${err.message}`);
    }
  };

  return (
    <div style={{
      display: 'flex',
      justifyContent: 'center',
      alignItems: 'center',
      height: '100vh',
      flexDirection: 'column',
      color: 'white',
      textAlign: 'center',
      padding: '20px',
      background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)'
    }}>
      <div style={{
        background: 'rgba(255, 255, 255, 0.1)',
        backdropFilter: 'blur(10px)',
        borderRadius: '20px',
        padding: '40px',
        maxWidth: '600px',
        width: '100%',
        boxShadow: '0 8px 32px 0 rgba(31, 38, 135, 0.37)',
        border: '1px solid rgba(255, 255, 255, 0.18)'
      }}>
        <h1 style={{ 
          fontSize: '2.5rem', 
          marginBottom: '20px',
          textShadow: '2px 2px 4px rgba(0,0,0,0.3)' 
        }}>
          🏆 Enterprise SQL Proxy System
        </h1>
        <p style={{ 
          fontSize: '1.2rem', 
          marginBottom: '30px',
          opacity: 0.9 
        }}>
          The Ultimate Enterprise-Grade SQL Query Execution Platform
        </p>
        
        <div style={{
          padding: '10px 20px',
          borderRadius: '10px',
          background: 'rgba(76, 175, 80, 0.3)',
          border: '1px solid rgba(76, 175, 80, 0.5)',
          marginBottom: '20px'
        }}>
          <strong>v2.0.0 | Production Ready</strong>
        </div>
        
        {loading ? (
          <div style={{ padding: '20px' }}>
            <div style={{
              width: '40px',
              height: '40px',
              border: '4px solid rgba(255,255,255,0.3)',
              borderTop: '4px solid white',
              borderRadius: '50%',
              animation: 'spin 1s linear infinite',
              margin: '0 auto 20px'
            }}></div>
            <p>Checking backend status...</p>
            <style>{`
              @keyframes spin {
                0% { transform: rotate(0deg); }
                100% { transform: rotate(360deg); }
              }
            `}</style>
          </div>
        ) : (
          <div style={{ 
            padding: '20px', 
            borderRadius: '10px', 
            background: status?.status === 'healthy' ? 
              'rgba(76, 175, 80, 0.3)' : 'rgba(244, 67, 54, 0.3)',
            border: `1px solid ${status?.status === 'healthy' ? 
              'rgba(76, 175, 80, 0.5)' : 'rgba(244, 67, 54, 0.5)'}`,
            marginBottom: '20px'
          }}>
            <div style={{ fontSize: '1.2rem', marginBottom: '10px' }}>
              <strong>Backend Status:</strong> {status?.status === 'healthy' ? '🟢 Healthy' : '🔴 Error'}
            </div>
            <div style={{ fontSize: '0.9rem', opacity: 0.8 }}>
              Version: {status?.version || 'Unknown'}
            </div>
            {status?.environment && (
              <div style={{ fontSize: '0.9rem', opacity: 0.8 }}>
                Environment: {status.environment}
              </div>
            )}
            {error && (
              <div style={{ 
                fontSize: '0.8rem', 
                color: '#ffcdd2', 
                marginTop: '10px',
                padding: '10px',
                background: 'rgba(244, 67, 54, 0.2)',
                borderRadius: '5px'
              }}>
                Error: {error}
              </div>
            )}
          </div>
        )}

        <div style={{ marginTop: '30px' }}>
          <button 
            onClick={() => window.open('/docs', '_blank')}
            style={{
              color: 'white',
              textDecoration: 'none',
              background: 'rgba(255, 255, 255, 0.2)',
              padding: '12px 24px',
              borderRadius: '10px',
              margin: '0 10px',
              display: 'inline-block',
              border: 'none',
              cursor: 'pointer',
              fontSize: '1rem',
              transition: 'all 0.3s ease'
            }}
            onMouseOver={(e) => e.target.style.background = 'rgba(255, 255, 255, 0.3)'}
            onMouseOut={(e) => e.target.style.background = 'rgba(255, 255, 255, 0.2)'}
          >
            📚 API Documentation
          </button>
          
          <button 
            onClick={handleAPITest}
            style={{
              color: 'white',
              textDecoration: 'none',
              background: 'rgba(255, 255, 255, 0.2)',
              padding: '12px 24px',
              borderRadius: '10px',
              margin: '0 10px',
              display: 'inline-block',
              border: 'none',
              cursor: 'pointer',
              fontSize: '1rem',
              transition: 'all 0.3s ease'
            }}
            onMouseOver={(e) => e.target.style.background = 'rgba(255, 255, 255, 0.3)'}
            onMouseOut={(e) => e.target.style.background = 'rgba(255, 255, 255, 0.2)'}
          >
            🧪 Test API
          </button>
        </div>

        <div style={{ 
          fontSize: '0.9rem', 
          opacity: 0.8, 
          marginTop: '30px',
          borderTop: '1px solid rgba(255, 255, 255, 0.2)',
          paddingTop: '20px'
        }}>
          <div style={{ marginBottom: '10px' }}>
            <strong>Created by:</strong> Teeksss
          </div>
          <div style={{ marginBottom: '10px' }}>
            <strong>Version:</strong> 2.0.0
          </div>
          <div style={{ marginBottom: '10px' }}>
            <strong>Build Date:</strong> 2025-05-30 08:05:44 UTC
          </div>
          <div style={{ marginBottom: '10px' }}>
            <strong>Status:</strong> 🚀 Production Ready
          </div>
          <div>
            <strong>Quality:</strong> 🌟 Enterprise Grade
          </div>
        </div>

        <div style={{ marginTop: '20px' }}>
          <button 
            onClick={handleRefresh}
            style={{
              color: 'white',
              background: 'rgba(255, 255, 255, 0.1)',
              padding: '8px 16px',
              borderRadius: '8px',
              border: '1px solid rgba(255, 255, 255, 0.3)',
              cursor: 'pointer',
              fontSize: '0.9rem'
            }}
          >
            🔄 Refresh Status
          </button>
        </div>
      </div>
    </div>
  );
}

export default App;
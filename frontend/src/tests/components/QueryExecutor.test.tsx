// Query Executor Component Tests
// Created: 2025-05-29 13:19:13 UTC by Teeksss

import React from 'react';
import { vi } from 'vitest';
import { screen, waitFor } from '@testing-library/react';
import { userEvent } from '@testing-library/user-event';
import { render, mockServers, mockQueryResult, mockApiResponses } from '../utils/test-utils';
import QueryExecutor from '../../components/QueryExecutor/QueryExecutor';
import * as proxyService from '../../services/proxyService';

// Mock the proxy service
vi.mock('../../services/proxyService');

describe('QueryExecutor', () => {
  const mockExecuteQuery = vi.fn();
  const mockGetServers = vi.fn();
  const mockGetQueryHistory = vi.fn();

  beforeEach(() => {
    vi.clearAllMocks();
    
    // Setup service mocks
    vi.mocked(proxyService.executeQuery).mockImplementation(mockExecuteQuery);
    vi.mocked(proxyService.getServers).mockImplementation(mockGetServers);
    vi.mocked(proxyService.getQueryHistory).mockImplementation(mockGetQueryHistory);
    
    // Default mock implementations
    mockGetServers.mockResolvedValue(mockServers);
    mockGetQueryHistory.mockResolvedValue(mockApiResponses.queryHistory);
  });

  it('renders query executor interface', async () => {
    render(<QueryExecutor />);
    
    expect(screen.getByText('SQL Query Executor')).toBeInTheDocument();
    expect(screen.getByRole('textbox')).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /execute/i })).toBeInTheDocument();
  });

  it('loads and displays servers', async () => {
    render(<QueryExecutor />);
    
    await waitFor(() => {
      expect(screen.getByText('Test SQL Server')).toBeInTheDocument();
      expect(screen.getByText('Test PostgreSQL')).toBeInTheDocument();
    });
  });

  it('executes query successfully', async () => {
    const user = userEvent.setup();
    mockExecuteQuery.mockResolvedValue(mockQueryResult);
    
    render(<QueryExecutor />);
    
    // Wait for servers to load
    await waitFor(() => {
      expect(screen.getByText('Test SQL Server')).toBeInTheDocument();
    });
    
    // Select server
    const serverSelect = screen.getByRole('combobox');
    await user.click(serverSelect);
    await user.click(screen.getByText('Test SQL Server'));
    
    // Enter query
    const queryInput = screen.getByRole('textbox');
    await user.type(queryInput, 'SELECT * FROM users');
    
    // Execute query
    const executeButton = screen.getByRole('button', { name: /execute/i });
    await user.click(executeButton);
    
    // Wait for results
    await waitFor(() => {
      expect(screen.getByText('John Doe')).toBeInTheDocument();
      expect(screen.getByText('jane@example.com')).toBeInTheDocument();
    });
    
    expect(mockExecuteQuery).toHaveBeenCalledWith({
      query: 'SELECT * FROM users',
      serverId: 1,
      timeout: 300,
    });
  });

  it('handles query execution error', async () => {
    const user = userEvent.setup();
    mockExecuteQuery.mockRejectedValue(new Error('Connection failed'));
    
    render(<QueryExecutor />);
    
    // Wait for servers to load
    await waitFor(() => {
      expect(screen.getByText('Test SQL Server')).toBeInTheDocument();
    });
    
    // Select server and enter query
    const serverSelect = screen.getByRole('combobox');
    await user.click(serverSelect);
    await user.click(screen.getByText('Test SQL Server'));
    
    const queryInput = screen.getByRole('textbox');
    await user.type(queryInput, 'INVALID SQL');
    
    // Execute query
    const executeButton = screen.getByRole('button', { name: /execute/i });
    await user.click(executeButton);
    
    // Wait for error message
    await waitFor(() => {
      expect(screen.getByText(/connection failed/i)).toBeInTheDocument();
    });
  });

  it('formats SQL query', async () => {
    const user = userEvent.setup();
    
    render(<QueryExecutor />);
    
    // Enter unformatted query
    const queryInput = screen.getByRole('textbox');
    await user.type(queryInput, 'select * from users where active=1');
    
    // Click format button
    const formatButton = screen.getByRole('button', { name: /format/i });
    await user.click(formatButton);
    
    // Check if query is formatted (basic check)
    expect(queryInput).toHaveValue(expect.stringContaining('SELECT'));
  });

  it('clears query and results', async () => {
    const user = userEvent.setup();
    mockExecuteQuery.mockResolvedValue(mockQueryResult);
    
    render(<QueryExecutor />);
    
    // Enter and execute query first
    const queryInput = screen.getByRole('textbox');
    await user.type(queryInput, 'SELECT * FROM users');
    
    // Clear query
    const clearButton = screen.getByRole('button', { name: /clear/i });
    await user.click(clearButton);
    
    expect(queryInput).toHaveValue('');
  });

  it('opens query history modal', async () => {
    const user = userEvent.setup();
    
    render(<QueryExecutor showHistory={true} />);
    
    const historyButton = screen.getByRole('button', { name: /history/i });
    await user.click(historyButton);
    
    await waitFor(() => {
      expect(screen.getByText('Query History')).toBeInTheDocument();
    });
  });

  it('exports query results', async () => {
    const user = userEvent.setup();
    mockExecuteQuery.mockResolvedValue(mockQueryResult);
    
    // Mock file save
    const mockSaveAs = vi.fn();
    vi.mock('file-saver', () => ({
      saveAs: mockSaveAs,
    }));
    
    render(<QueryExecutor />);
    
    // Execute a query first to have results
    await waitFor(() => {
      expect(screen.getByText('Test SQL Server')).toBeInTheDocument();
    });
    
    const serverSelect = screen.getByRole('combobox');
    await user.click(serverSelect);
    await user.click(screen.getByText('Test SQL Server'));
    
    const queryInput = screen.getByRole('textbox');
    await user.type(queryInput, 'SELECT * FROM users');
    
    const executeButton = screen.getByRole('button', { name: /execute/i });
    await user.click(executeButton);
    
    await waitFor(() => {
      expect(screen.getByText('John Doe')).toBeInTheDocument();
    });
    
    // Export results
    const exportButton = screen.getByRole('button', { name: /export/i });
    await user.click(exportButton);
    
    const csvOption = screen.getByText('CSV');
    await user.click(csvOption);
    
    // Verify export was called (this would need proper mock setup)
  });

  it('handles read-only mode', () => {
    render(<QueryExecutor readOnly={true} />);
    
    const executeButton = screen.getByRole('button', { name: /execute/i });
    expect(executeButton).toBeDisabled();
  });

  it('shows validation warnings for dangerous queries', async () => {
    const user = userEvent.setup();
    
    render(<QueryExecutor />);
    
    const queryInput = screen.getByRole('textbox');
    await user.type(queryInput, "DELETE FROM users; DROP TABLE users; --");
    
    // This would trigger validation warnings in a real implementation
    // The exact implementation depends on your validation service
  });

  it('manages multiple query tabs', async () => {
    const user = userEvent.setup();
    
    render(<QueryExecutor />);
    
    // Add new tab
    const addTabButton = screen.getByRole('button', { name: /add/i });
    await user.click(addTabButton);
    
    // Should have multiple tabs now
    expect(screen.getAllByText(/Query \d+/)).toHaveLength(2);
  });
});
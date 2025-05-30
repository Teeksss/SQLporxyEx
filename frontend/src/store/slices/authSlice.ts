/**
 * Authentication Redux Slice - Final Version
 * Created: 2025-05-29 14:42:21 UTC by Teeksss
 */

import { createSlice, createAsyncThunk, PayloadAction } from '@reduxjs/toolkit';
import { authAPI } from '../../services/api/authAPI';

// Types
export interface User {
  id: number;
  username: string;
  email: string;
  firstName: string;
  lastName: string;
  displayName: string;
  role: 'admin' | 'analyst' | 'powerbi' | 'readonly';
  status: string;
  isActive: boolean;
  isVerified: boolean;
  lastLoginAt?: string;
  createdAt: string;
  preferences?: Record<string, any>;
}

export interface AuthState {
  user: User | null;
  accessToken: string | null;
  refreshToken: string | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  error: string | null;
  loginAttempts: number;
  lastLoginTime?: string;
  tokenExpiresAt?: string;
}

// Initial state
const initialState: AuthState = {
  user: null,
  accessToken: null,
  refreshToken: null,
  isAuthenticated: false,
  isLoading: false,
  error: null,
  loginAttempts: 0,
};

// Async thunks
export const login = createAsyncThunk(
  'auth/login',
  async (credentials: { username: string; password: string }, { rejectWithValue }) => {
    try {
      const response = await authAPI.login(credentials);
      
      // Store tokens in localStorage
      localStorage.setItem('esp_access_token', response.access_token);
      localStorage.setItem('esp_refresh_token', response.refresh_token);
      
      return response;
    } catch (error: any) {
      return rejectWithValue(error.response?.data?.detail || 'Login failed');
    }
  }
);

export const logout = createAsyncThunk('auth/logout', async (_, { dispatch }) => {
  try {
    await authAPI.logout();
  } catch (error) {
    // Log error but don't block logout
    console.error('Logout API call failed:', error);
  } finally {
    // Always clear local storage and reset state
    localStorage.removeItem('esp_access_token');
    localStorage.removeItem('esp_refresh_token');
    dispatch(resetAuth());
  }
});

export const refreshToken = createAsyncThunk(
  'auth/refreshToken',
  async (_, { getState, rejectWithValue }) => {
    try {
      const state = getState() as { auth: AuthState };
      const refreshTokenValue = state.auth.refreshToken;
      
      if (!refreshTokenValue) {
        return rejectWithValue('No refresh token available');
      }
      
      const response = await authAPI.refreshToken(refreshTokenValue);
      
      // Update tokens in localStorage
      localStorage.setItem('esp_access_token', response.access_token);
      localStorage.setItem('esp_refresh_token', response.refresh_token);
      
      return response;
    } catch (error: any) {
      return rejectWithValue(error.response?.data?.detail || 'Token refresh failed');
    }
  }
);

export const getCurrentUser = createAsyncThunk(
  'auth/getCurrentUser',
  async (_, { rejectWithValue }) => {
    try {
      const response = await authAPI.getCurrentUser();
      return response;
    } catch (error: any) {
      return rejectWithValue(error.response?.data?.detail || 'Failed to get user info');
    }
  }
);

export const changePassword = createAsyncThunk(
  'auth/changePassword',
  async (
    passwords: { oldPassword: string; newPassword: string },
    { rejectWithValue }
  ) => {
    try {
      await authAPI.changePassword(passwords);
      return { success: true };
    } catch (error: any) {
      return rejectWithValue(error.response?.data?.detail || 'Password change failed');
    }
  }
);

export const validateToken = createAsyncThunk(
  'auth/validateToken',
  async (_, { rejectWithValue }) => {
    try {
      const response = await authAPI.validateToken();
      return response;
    } catch (error: any) {
      return rejectWithValue(error.response?.data?.detail || 'Token validation failed');
    }
  }
);

// Auth slice
const authSlice = createSlice({
  name: 'auth',
  initialState,
  reducers: {
    resetAuth: (state) => {
      state.user = null;
      state.accessToken = null;
      state.refreshToken = null;
      state.isAuthenticated = false;
      state.isLoading = false;
      state.error = null;
      state.loginAttempts = 0;
      state.lastLoginTime = undefined;
      state.tokenExpiresAt = undefined;
    },
    clearError: (state) => {
      state.error = null;
    },
    setTokens: (state, action: PayloadAction<{ accessToken: string; refreshToken: string }>) => {
      state.accessToken = action.payload.accessToken;
      state.refreshToken = action.payload.refreshToken;
      state.isAuthenticated = true;
    },
    updateUser: (state, action: PayloadAction<Partial<User>>) => {
      if (state.user) {
        state.user = { ...state.user, ...action.payload };
      }
    },
    setLoading: (state, action: PayloadAction<boolean>) => {
      state.isLoading = action.payload;
    },
  },
  extraReducers: (builder) => {
    // Login
    builder
      .addCase(login.pending, (state) => {
        state.isLoading = true;
        state.error = null;
      })
      .addCase(login.fulfilled, (state, action) => {
        state.isLoading = false;
        state.user = action.payload.user;
        state.accessToken = action.payload.access_token;
        state.refreshToken = action.payload.refresh_token;
        state.isAuthenticated = true;
        state.error = null;
        state.loginAttempts = 0;
        state.lastLoginTime = new Date().toISOString();
        
        // Calculate token expiration
        const expiresIn = action.payload.expires_in * 1000; // Convert to milliseconds
        state.tokenExpiresAt = new Date(Date.now() + expiresIn).toISOString();
      })
      .addCase(login.rejected, (state, action) => {
        state.isLoading = false;
        state.error = action.payload as string;
        state.loginAttempts += 1;
      });

    // Logout
    builder
      .addCase(logout.pending, (state) => {
        state.isLoading = true;
      })
      .addCase(logout.fulfilled, (state) => {
        // State is reset by the resetAuth action dispatched in the thunk
        state.isLoading = false;
      })
      .addCase(logout.rejected, (state) => {
        // Even if logout fails, reset the state
        state.isLoading = false;
      });

    // Refresh Token
    builder
      .addCase(refreshToken.pending, (state) => {
        state.isLoading = true;
      })
      .addCase(refreshToken.fulfilled, (state, action) => {
        state.isLoading = false;
        state.accessToken = action.payload.access_token;
        state.refreshToken = action.payload.refresh_token;
        state.error = null;
        
        // Update token expiration
        const expiresIn = action.payload.expires_in * 1000;
        state.tokenExpiresAt = new Date(Date.now() + expiresIn).toISOString();
      })
      .addCase(refreshToken.rejected, (state, action) => {
        state.isLoading = false;
        state.error = action.payload as string;
        // If refresh fails, user needs to login again
        state.accessToken = null;
        state.refreshToken = null;
        state.isAuthenticated = false;
        state.user = null;
      });

    // Get Current User
    builder
      .addCase(getCurrentUser.pending, (state) => {
        state.isLoading = true;
      })
      .addCase(getCurrentUser.fulfilled, (state, action) => {
        state.isLoading = false;
        state.user = action.payload;
        state.error = null;
      })
      .addCase(getCurrentUser.rejected, (state, action) => {
        state.isLoading = false;
        state.error = action.payload as string;
      });

    // Change Password
    builder
      .addCase(changePassword.pending, (state) => {
        state.isLoading = true;
        state.error = null;
      })
      .addCase(changePassword.fulfilled, (state) => {
        state.isLoading = false;
        state.error = null;
      })
      .addCase(changePassword.rejected, (state, action) => {
        state.isLoading = false;
        state.error = action.payload as string;
      });

    // Validate Token
    builder
      .addCase(validateToken.pending, (state) => {
        state.isLoading = true;
      })
      .addCase(validateToken.fulfilled, (state, action) => {
        state.isLoading = false;
        state.isAuthenticated = action.payload.valid;
        state.error = null;
      })
      .addCase(validateToken.rejected, (state, action) => {
        state.isLoading = false;
        state.error = action.payload as string;
        state.isAuthenticated = false;
      });
  },
});

// Actions
export const { resetAuth, clearError, setTokens, updateUser, setLoading } = authSlice.actions;

// Selectors
export const selectAuth = (state: { auth: AuthState }) => state.auth;
export const selectUser = (state: { auth: AuthState }) => state.auth.user;
export const selectIsAuthenticated = (state: { auth: AuthState }) => state.auth.isAuthenticated;
export const selectIsLoading = (state: { auth: AuthState }) => state.auth.isLoading;
export const selectError = (state: { auth: AuthState }) => state.auth.error;
export const selectAccessToken = (state: { auth: AuthState }) => state.auth.accessToken;

export default authSlice.reducer;
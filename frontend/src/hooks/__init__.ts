/**
 * Hooks Module - React Hook Exports
 * Created: 2025-05-29 14:11:08 UTC by Teeksss
 */

// Authentication Hooks
export { useAuth, AuthProvider } from './useAuth';

// API Hooks
export { default as useApi } from './useApi';
export { default as useQuery } from './useQuery';
export { default as useMutation } from './useMutation';

// UI Hooks
export { default as useTheme } from './useTheme';
export { default as useLocalStorage } from './useLocalStorage';
export { default as useSessionStorage } from './useSessionStorage';
export { default as useDebounce } from './useDebounce';
export { default as useAsync } from './useAsync';

// Form Hooks
export { default as useForm } from './useForm';
export { default as useValidation } from './useValidation';

// Data Hooks
export { default as usePagination } from './usePagination';
export { default as useFilter } from './useFilter';
export { default as useSort } from './useSort';
export { default as useSearch } from './useSearch';

// Utility Hooks
export { default as useWebSocket } from './useWebSocket';
export { default as useNotification } from './useNotification';
export { default as useConfirm } from './useConfirm';
export { default as usePermissions } from './usePermissions';

// Hook metadata
export const HOOK_METADATA = {
    version: '2.0.0',
    author: 'Teeksss',
    totalHooks: 16,
    categories: {
        auth: 1,
        api: 3,
        ui: 5,
        form: 2,
        data: 4,
        utility: 4
    },
    lastUpdated: '2025-05-29T14:11:08Z'
};
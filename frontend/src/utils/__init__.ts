/**
 * Utils Module - Utility Function Exports
 * Created: 2025-05-29 14:11:08 UTC by Teeksss
 */

// Date/Time Utils
export {
    formatDate,
    formatDateTime,
    formatRelativeTime,
    parseDate,
    addDays,
    subtractDays,
    isToday,
    isYesterday,
    getDateRange
} from './dateUtils';

// Format Utils
export {
    formatNumber,
    formatCurrency,
    formatPercentage,
    formatFileSize,
    formatDuration,
    truncateText,
    capitalizeFirst,
    camelToSnake,
    snakeToCamel
} from './formatUtils';

// Validation Utils
export {
    validateEmail,
    validatePassword,
    validateURL,
    validatePhone,
    validateRequired,
    validateLength,
    validatePattern,
    createValidator
} from './validationUtils';

// String Utils
export {
    generateId,
    slugify,
    sanitizeHTML,
    escapeRegex,
    pluralize,
    randomString,
    hashString,
    compareStrings
} from './stringUtils';

// Array Utils
export {
    chunk,
    unique,
    groupBy,
    sortBy,
    filterBy,
    findBy,
    flatten,
    intersection,
    difference,
    shuffle
} from './arrayUtils';

// Object Utils
export {
    deepClone,
    deepMerge,
    pick,
    omit,
    isEmpty,
    isEqual,
    flattenObject,
    unflattenObject,
    safeGet,
    safeSet
} from './objectUtils';

// API Utils
export {
    buildQueryString,
    parseQueryString,
    createApiUrl,
    handleApiError,
    extractErrorMessage,
    retryRequest
} from './apiUtils';

// Storage Utils
export {
    getLocalStorage,
    setLocalStorage,
    removeLocalStorage,
    clearLocalStorage,
    getSessionStorage,
    setSessionStorage,
    removeSessionStorage,
    clearSessionStorage
} from './storageUtils';

// Constants
export const CONSTANTS = {
    DATE_FORMATS: {
        SHORT: 'MMM DD, YYYY',
        LONG: 'MMMM DD, YYYY',
        WITH_TIME: 'MMM DD, YYYY HH:mm',
        ISO: 'YYYY-MM-DDTHH:mm:ss.SSSZ'
    },
    FILE_SIZES: {
        KB: 1024,
        MB: 1024 * 1024,
        GB: 1024 * 1024 * 1024
    },
    REGEX_PATTERNS: {
        EMAIL: /^[^\s@]+@[^\s@]+\.[^\s@]+$/,
        PHONE: /^\+?[\d\s\-\(\)]+$/,
        URL: /^https?:\/\/.+/,
        PASSWORD: /^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[@$!%*?&])[A-Za-z\d@$!%*?&]/
    }
};

// Utility metadata
export const UTILS_METADATA = {
    version: '2.0.0',
    author: 'Teeksss',
    totalFunctions: 68,
    categories: {
        date: 9,
        format: 9,
        validation: 8,
        string: 8,
        array: 10,
        object: 10,
        api: 6,
        storage: 8
    },
    lastUpdated: '2025-05-29T14:11:08Z'
};
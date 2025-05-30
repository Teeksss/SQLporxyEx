/**
 * Redux Store Configuration - Final Version
 * Created: 2025-05-29 14:42:21 UTC by Teeksss
 */

import { configureStore } from '@reduxjs/toolkit';
import { persistStore, persistReducer } from 'redux-persist';
import storage from 'redux-persist/lib/storage';
import { combineReducers } from '@reduxjs/toolkit';

// Slice imports
import authSlice from './slices/authSlice';
import querySlice from './slices/querySlice';
import serverSlice from './slices/serverSlice';
import notificationSlice from './slices/notificationSlice';
import uiSlice from './slices/uiSlice';
import settingsSlice from './slices/settingsSlice';

// Persist configuration
const persistConfig = {
  key: 'esp-root',
  storage,
  whitelist: ['auth', 'settings', 'ui'], // Only persist these slices
  version: 1,
};

// Root reducer
const rootReducer = combineReducers({
  auth: authSlice,
  query: querySlice,
  server: serverSlice,
  notification: notificationSlice,
  ui: uiSlice,
  settings: settingsSlice,
});

// Persisted reducer
const persistedReducer = persistReducer(persistConfig, rootReducer);

// Store configuration
export const store = configureStore({
  reducer: persistedReducer,
  middleware: (getDefaultMiddleware) =>
    getDefaultMiddleware({
      serializableCheck: {
        ignoredActions: ['persist/PERSIST', 'persist/REHYDRATE'],
        ignoredPaths: ['register'],
      },
    }),
  devTools: process.env.NODE_ENV !== 'production',
});

// Persistor
export const persistor = persistStore(store);

// Types
export type RootState = ReturnType<typeof store.getState>;
export type AppDispatch = typeof store.dispatch;

// Typed hooks
import { useDispatch, useSelector, TypedUseSelectorHook } from 'react-redux';

export const useAppDispatch = () => useDispatch<AppDispatch>();
export const useAppSelector: TypedUseSelectorHook<RootState> = useSelector;

export default store;
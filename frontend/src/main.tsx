import React from 'react';
import ReactDOM from 'react-dom/client';
import { App } from './app/App';
import { bootstrapMocks } from './shared/api/mocks';
import './index.css';

// Демо-режим: если моки включены — сразу «логиним» пользователя демо-токеном.
bootstrapMocks();

ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>,
);

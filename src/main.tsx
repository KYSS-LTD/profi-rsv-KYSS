import React from 'react';
import ReactDOM from 'react-dom/client';
import { App } from '@/app/App';
import { Providers } from '@/app/providers';
import { initTelegramShell } from '@/shared/lib/telegram';
import { registerServiceWorker } from '@/shared/lib/pwa';
import './index.css';

initTelegramShell();
registerServiceWorker();

ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <Providers>
      <App />
    </Providers>
  </React.StrictMode>,
);

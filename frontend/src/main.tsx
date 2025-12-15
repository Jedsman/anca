import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import './index.css'
import App from './App.tsx'

console.log("Main.tsx executing...");
const root = document.getElementById('root');
console.log("Root element:", root);

if (!root) {
    console.error("ROOT ELEMENT NOT FOUND");
} else {
    createRoot(root).render(
      <StrictMode>
        <App />
      </StrictMode>,
    )
}

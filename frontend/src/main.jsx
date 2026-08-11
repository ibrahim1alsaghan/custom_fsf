import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import { BrowserRouter, Routes, Route } from 'react-router-dom'
import Landing from './pages/Landing'
import Login from './pages/Signin'
import ForgotPassword from './pages/ForgotPassword'
import './index.css'

// Mount React app
const rootElement = document.getElementById('root')

if (rootElement) {
    createRoot(rootElement).render(
      <StrictMode>
        <BrowserRouter>
          <Routes>
            <Route path="/" element={<Landing />} />
            <Route path="/landing" element={<Landing />} />
            <Route path="/signin" element={<Login />} />
            <Route path="/forgot-password" element={<ForgotPassword />} />
          </Routes>
        </BrowserRouter>
      </StrictMode>
    )
  }

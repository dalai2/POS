import React from 'react'
import ReactDOM from 'react-dom/client'
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import './styles.css'
import LoginPage from './pages/LoginPage'
import ProductsPage from './pages/ProductsPage'
import UsersPage from './pages/UsersPage'
import BillingPage from './pages/BillingPage'
import DashboardPage from './pages/DashboardPage'
import SalesPage from './pages/SalesPage'
import SalesHistoryPage from './pages/SalesHistoryPage'
import MetalRatesPage from './pages/MetalRatesPage'
import CreditsPage from './pages/CreditsPage'
import ReportsPage from './pages/ReportsPage'
import PedidosPage from './pages/PedidosPage'
import GestionPedidosPage from './pages/GestionPedidosPage'

ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <BrowserRouter>
      <Routes>
        <Route path="/login" element={<LoginPage />} />
        <Route path="/" element={<DashboardPage />} />
        <Route path="/products" element={<ProductsPage />} />
        <Route path="/users" element={<UsersPage />} />
        <Route path="/billing" element={<BillingPage />} />
        <Route path="/sales" element={<SalesPage />} />
        <Route path="/pedidos" element={<PedidosPage />} />
        <Route path="/gestion-pedidos" element={<GestionPedidosPage />} />
        <Route path="/sales/history" element={<SalesHistoryPage />} />
        <Route path="/metal-rates" element={<MetalRatesPage />} />
        <Route path="/credits" element={<CreditsPage />} />
        <Route path="/reports" element={<ReportsPage />} />
        <Route path="*" element={<Navigate to="/login" replace />} />
      </Routes>
    </BrowserRouter>
  </React.StrictMode>
)



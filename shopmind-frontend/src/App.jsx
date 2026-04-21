// src/App.jsx
import { Suspense, lazy } from 'react'
import { BrowserRouter, Routes, Route } from 'react-router-dom'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { Toaster } from 'react-hot-toast'
import Navbar from './components/layout/Navbar'
import CartDrawer from './components/cart/CartDrawer'
import { Spinner } from './components/ui'

const HomePage = lazy(() => import('./pages/HomePage'))
const ProductsPage = lazy(() => import('./pages/ProductsPage'))
const RecommendationsPage = lazy(() => import('./pages/RecommendationsPage'))
const OrdersPage = lazy(() => import('./pages/OrdersPage'))
const AuthPage = lazy(() => import('./pages/AuthPage'))

const queryClient = new QueryClient({
    defaultOptions: { queries: { retry: 1, refetchOnWindowFocus: false } },
})

function PageLoader() {
    return (
        <div style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', minHeight: '60vh' }}>
            <Spinner size={32} />
        </div>
    )
}

// Wrapper components for named exports
const LoginPage = lazy(() => import('./pages/AuthPage').then(m => ({ default: m.LoginPage })))
const RegisterPage = lazy(() => import('./pages/AuthPage').then(m => ({ default: m.RegisterPage })))

export default function App() {
    return (
        <QueryClientProvider client={queryClient}>
            <BrowserRouter>
                <Navbar />
                <CartDrawer />
                <main>
                    <Suspense fallback={<PageLoader />}>
                        <Routes>
                            <Route path="/" element={<HomePage />} />
                            <Route path="/products" element={<ProductsPage />} />
                            <Route path="/products/:id" element={<ProductsPage />} />
                            <Route path="/recommendations" element={<RecommendationsPage />} />
                            <Route path="/orders" element={<OrdersPage />} />
                            <Route path="/login" element={<LoginPage />} />
                            <Route path="/register" element={<RegisterPage />} />
                            <Route path="*" element={
                                <div style={{ textAlign: 'center', padding: '6rem 1rem' }}>
                                    <p style={{ fontSize: '4rem', marginBottom: '1rem' }}>404</p>
                                    <h2 style={{ fontFamily: 'var(--font-display)', fontSize: '2rem', marginBottom: '1rem' }}>Page not found</h2>
                                    <a href="/" style={{ color: 'var(--accent)' }}>← Back to home</a>
                                </div>
                            } />
                        </Routes>
                    </Suspense>
                </main>
                <footer style={{ padding: '2.5rem 1.5rem', borderTop: '1px solid var(--border)', textAlign: 'center', marginTop: '4rem' }}>
                    <div style={{ maxWidth: 'var(--content-max)', margin: '0 auto' }}>
                        <p style={{ fontFamily: 'var(--font-display)', fontSize: '1.25rem', marginBottom: 4 }}>ShopMind AI</p>
                        <p style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>
                            Powered by Nemotron · Built with FastAPI + Valkey + React
                        </p>
                    </div>
                </footer>
                <Toaster
                    position="bottom-right"
                    toastOptions={{
                        style: {
                            background: 'var(--bg-raised)', color: 'var(--text-primary)',
                            border: '1px solid var(--border)', borderRadius: 'var(--radius-sm)',
                            fontSize: '0.875rem', boxShadow: 'var(--shadow-lg)',
                        },
                        success: { iconTheme: { primary: 'var(--success)', secondary: 'var(--bg-raised)' } },
                        error: { iconTheme: { primary: 'var(--error)', secondary: 'var(--bg-raised)' } },
                    }}
                />
            </BrowserRouter>
        </QueryClientProvider>
    )
}
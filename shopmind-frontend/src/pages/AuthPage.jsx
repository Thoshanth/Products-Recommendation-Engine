// src/pages/AuthPage.jsx — Login & Register

import { useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { Eye, EyeOff, Sparkles, ArrowRight } from 'lucide-react'
import { authAPI, cartAPI } from '../services/api'
import { useAuthStore, useCartStore } from '../store'
import { Button, Input } from '../components/ui'
import toast from 'react-hot-toast'

export function LoginPage() {
    const [form, setForm] = useState({ email: '', password: '' })
    const [showPw, setShowPw] = useState(false)
    const [loading, setLoading] = useState(false)
    const { setAuth } = useAuthStore()
    const { setCart } = useCartStore()
    const navigate = useNavigate()

    async function handleSubmit(e) {
        e.preventDefault()
        setLoading(true)
        try {
            const { data } = await authAPI.login(form)
            setAuth(data.user, data.tokens)
            // Fetch cart
            cartAPI.get().then(r => setCart(r.data)).catch(() => { })
            toast.success(`Welcome back, ${data.user.name}!`)
            navigate('/')
        } catch (err) {
            toast.error(err.response?.data?.detail ?? 'Login failed')
        } finally {
            setLoading(false)
        }
    }

    return (
        <AuthLayout
            title="Welcome back"
            subtitle="Sign in to your ShopMind account"
            footer={<>No account? <Link to="/register" style={{ color: 'var(--accent)' }}>Create one →</Link></>}
        >
            <form onSubmit={handleSubmit} style={{ display: 'flex', flexDirection: 'column', gap: '1.25rem' }}>
                <Input
                    label="Email"
                    type="email"
                    placeholder="you@example.com"
                    value={form.email}
                    onChange={e => setForm(f => ({ ...f, email: e.target.value }))}
                    required
                />
                <div>
                    <Input
                        label="Password"
                        type={showPw ? 'text' : 'password'}
                        placeholder="••••••••"
                        value={form.password}
                        onChange={e => setForm(f => ({ ...f, password: e.target.value }))}
                        required
                    />
                    <button type="button" onClick={() => setShowPw(v => !v)}
                        style={{
                            position: 'absolute', right: 12, top: '50%', transform: 'translateY(-50%)',
                            background: 'none', border: 'none', color: 'var(--text-muted)', cursor: 'pointer'
                        }}>
                        {showPw ? <EyeOff size={16} /> : <Eye size={16} />}
                    </button>
                </div>
                <Button type="submit" loading={loading} size="lg" style={{ width: '100%', marginTop: 4 }}>
                    Sign In <ArrowRight size={16} />
                </Button>
            </form>
        </AuthLayout>
    )
}

export function RegisterPage() {
    const [form, setForm] = useState({ name: '', email: '', password: '', phone: '' })
    const [showPw, setShowPw] = useState(false)
    const [loading, setLoading] = useState(false)
    const { setAuth } = useAuthStore()
    const navigate = useNavigate()

    async function handleSubmit(e) {
        e.preventDefault()
        if (form.password.length < 8) {
            toast.error('Password must be at least 8 characters')
            return
        }
        setLoading(true)
        try {
            const { data } = await authAPI.register(form)
            setAuth(data.user, data.tokens)
            toast.success('Account created! Welcome to ShopMind 🎉')
            navigate('/')
        } catch (err) {
            toast.error(err.response?.data?.detail ?? 'Registration failed')
        } finally {
            setLoading(false)
        }
    }

    return (
        <AuthLayout
            title="Create account"
            subtitle="Join ShopMind AI — it's free"
            footer={<>Already have an account? <Link to="/login" style={{ color: 'var(--accent)' }}>Sign in →</Link></>}
        >
            <form onSubmit={handleSubmit} style={{ display: 'flex', flexDirection: 'column', gap: '1.25rem' }}>
                <Input label="Full Name" placeholder="Arjun Sharma" value={form.name}
                    onChange={e => setForm(f => ({ ...f, name: e.target.value }))} required />
                <Input label="Email" type="email" placeholder="you@example.com" value={form.email}
                    onChange={e => setForm(f => ({ ...f, email: e.target.value }))} required />
                <Input label="Phone (optional)" type="tel" placeholder="+91-9876543210" value={form.phone}
                    onChange={e => setForm(f => ({ ...f, phone: e.target.value }))} />
                <div style={{ position: 'relative' }}>
                    <Input label="Password" type={showPw ? 'text' : 'password'} placeholder="Min 8 characters"
                        value={form.password} onChange={e => setForm(f => ({ ...f, password: e.target.value }))} required />
                    <button type="button" onClick={() => setShowPw(v => !v)}
                        style={{
                            position: 'absolute', right: 12, bottom: 10,
                            background: 'none', border: 'none', color: 'var(--text-muted)', cursor: 'pointer'
                        }}>
                        {showPw ? <EyeOff size={16} /> : <Eye size={16} />}
                    </button>
                </div>
                <Button type="submit" loading={loading} size="lg" style={{ width: '100%', marginTop: 4 }}>
                    Create Account <ArrowRight size={16} />
                </Button>
                <p style={{ fontSize: '0.75rem', color: 'var(--text-muted)', textAlign: 'center' }}>
                    By signing up you agree to our Terms of Service.
                </p>
            </form>
        </AuthLayout>
    )
}

function AuthLayout({ title, subtitle, children, footer }) {
    return (
        <div style={{
            minHeight: 'calc(100vh - var(--nav-height))',
            display: 'flex', alignItems: 'center', justifyContent: 'center',
            padding: '2rem 1rem',
        }}>
            <div style={{ width: '100%', maxWidth: 420 }} className="fade-up">
                {/* Logo */}
                <div style={{ textAlign: 'center', marginBottom: '2rem' }}>
                    <div style={{
                        width: 52, height: 52, borderRadius: 14,
                        background: 'var(--accent)', margin: '0 auto 1rem',
                        display: 'flex', alignItems: 'center', justifyContent: 'center',
                        boxShadow: 'var(--shadow-accent)',
                    }}>
                        <Sparkles size={24} color="var(--text-inverse)" />
                    </div>
                    <h1 style={{ fontFamily: 'var(--font-display)', fontSize: '1.875rem', marginBottom: 6 }}>{title}</h1>
                    <p style={{ color: 'var(--text-secondary)', fontSize: '0.9rem' }}>{subtitle}</p>
                </div>

                {/* Card */}
                <div style={{
                    background: 'var(--bg-surface)', border: '1px solid var(--border)',
                    borderRadius: 'var(--radius-lg)', padding: '2rem',
                    boxShadow: 'var(--shadow-lg)',
                }}>
                    {children}
                </div>

                {footer && (
                    <p style={{ textAlign: 'center', marginTop: '1.25rem', fontSize: '0.875rem', color: 'var(--text-secondary)' }}>
                        {footer}
                    </p>
                )}
            </div>
        </div>
    )
}
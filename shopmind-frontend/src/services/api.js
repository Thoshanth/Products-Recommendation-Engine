// src/services/api.js — Axios instance + all API calls

import axios from 'axios'

const api = axios.create({
    baseURL: '/api/v1',
    timeout: 15000,
})

// ── Auth token injection ────────────────────────────────────────────────────
api.interceptors.request.use(config => {
    const token = localStorage.getItem('access_token')
    if (token) config.headers.Authorization = `Bearer ${token}`
    return config
})

// ── Auto-refresh on 401 ──────────────────────────────────────────────────────
api.interceptors.response.use(
    res => res,
    async err => {
        const original = err.config
        if (err.response?.status === 401 && !original._retry) {
            original._retry = true
            const refresh = localStorage.getItem('refresh_token')
            if (refresh) {
                try {
                    const { data } = await axios.post('/api/v1/auth/refresh', { refresh_token: refresh })
                    localStorage.setItem('access_token', data.tokens.access_token)
                    localStorage.setItem('refresh_token', data.tokens.refresh_token)
                    original.headers.Authorization = `Bearer ${data.tokens.access_token}`
                    return api(original)
                } catch {
                    localStorage.clear()
                    window.location.href = '/login'
                }
            }
        }
        return Promise.reject(err)
    }
)

// ── Auth ─────────────────────────────────────────────────────────────────────
export const authAPI = {
    register: data => api.post('/auth/register', data),
    login: data => api.post('/auth/login', data),
    logout: token => api.post('/auth/logout', { refresh_token: token }),
    refresh: token => api.post('/auth/refresh', { refresh_token: token }),
}

// ── Products ─────────────────────────────────────────────────────────────────
export const productsAPI = {
    list: params => api.get('/products', { params }),
    get: id => api.get(`/products/${id}`),
    featured: () => api.get('/products/featured'),
    topRated: () => api.get('/products/top-rated'),
    search: params => api.get('/products/search', { params }),
    byCategory: (cat, params) => api.get(`/products/category/${cat}`, { params }),
}

// ── Recommendations ──────────────────────────────────────────────────────────
export const recoAPI = {
    personalized: params => api.get('/recommendations/me', { params }),
    similar: id => api.get(`/recommendations/similar/${id}`),
    trending: period => api.get('/recommendations/trending', { params: { period } }),
    popular: () => api.get('/recommendations/popular'),
    byCategory: cat => api.get(`/recommendations/category/${cat}`),
    newArrivals: () => api.get('/recommendations/new-arrivals'),
}

// ── Cart ─────────────────────────────────────────────────────────────────────
export const cartAPI = {
    get: () => api.get('/cart'),
    add: data => api.post('/cart/items', data),
    updateQty: (id, data) => api.patch(`/cart/items/${id}`, data),
    remove: id => api.delete(`/cart/items/${id}`),
    clear: () => api.delete('/cart'),
    applyCoupon: code => api.post('/cart/coupon', { code }),
    removeCoupon: () => api.delete('/cart/coupon'),
}

// ── Orders ───────────────────────────────────────────────────────────────────
export const ordersAPI = {
    place: data => api.post('/orders', data),
    list: params => api.get('/orders', { params }),
    get: id => api.get(`/orders/${id}`),
    cancel: (id, reason) => api.post(`/orders/${id}/cancel`, { reason }),
}

// ── Users ─────────────────────────────────────────────────────────────────────
export const usersAPI = {
    me: () => api.get('/users/me'),
    update: data => api.patch('/users/me', data),
    stats: () => api.get('/users/me/stats'),
    loyalty: () => api.get('/users/me/loyalty'),
    addresses: () => api.get('/users/me/addresses'),
    addAddress: data => api.post('/users/me/addresses', data),
    deleteAddress: id => api.delete(`/users/me/addresses/${id}`),
    wishlist: () => api.get('/users/me/wishlist'),
    addWishlist: id => api.post(`/users/me/wishlist/${id}`),
    removeWishlist: id => api.delete(`/users/me/wishlist/${id}`),
}

// ── Reviews ──────────────────────────────────────────────────────────────────
export const reviewsAPI = {
    getForProduct: (id, params) => api.get(`/reviews/product/${id}`, { params }),
    create: data => api.post('/reviews', data),
    voteHelpful: (id, v) => api.post(`/reviews/${id}/helpful`, { is_helpful: v }),
    delete: id => api.delete(`/reviews/${id}`),
    mine: () => api.get('/reviews/me'),
}

// ── Behavior ─────────────────────────────────────────────────────────────────
export const behaviorAPI = {
    track: data => api.post('/behavior/track', data).catch(() => { }), // fire & forget
}

export default api
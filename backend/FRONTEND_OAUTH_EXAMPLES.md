# Frontend OAuth Integration Examples for LogoKraft

## 🚀 Complete Frontend OAuth Implementation

This guide provides production-ready frontend code for integrating Google and GitHub OAuth with your LogoKraft backend.

## 📱 React.js + Next.js Implementation

### 1. Project Setup

```bash
# Create Next.js project with TypeScript
npx create-next-app@latest logokraft-frontend --typescript --tailwind --app --eslint

# Install dependencies
cd logokraft-frontend
npm install @supabase/supabase-js axios react-hook-form @hookform/resolvers zod
npm install lucide-react @headlessui/react
npm install js-cookie @types/js-cookie
```

### 2. Environment Configuration

```bash
# .env.local
NEXT_PUBLIC_API_URL=http://localhost:8000
NEXT_PUBLIC_SUPABASE_URL=https://your-project.supabase.co
NEXT_PUBLIC_SUPABASE_ANON_KEY=your_anon_key_here
NEXT_PUBLIC_FRONTEND_URL=http://localhost:3000
```

### 3. API Service Layer

```typescript
// lib/api.ts
import axios from 'axios'
import Cookies from 'js-cookie'

const API_BASE = process.env.NEXT_PUBLIC_API_URL

// Create axios instance with interceptors
const api = axios.create({
  baseURL: API_BASE,
  timeout: 10000,
})

// Add auth token to requests
api.interceptors.request.use((config) => {
  const token = Cookies.get('access_token')
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

// Handle token expiration
api.interceptors.response.use(
  (response) => response,
  async (error) => {
    if (error.response?.status === 401) {
      // Token expired, try to refresh
      const refreshToken = Cookies.get('refresh_token')
      if (refreshToken) {
        try {
          const { data } = await refreshAuthToken(refreshToken)
          setAuthTokens(data.access_token, data.refresh_token)
          // Retry the original request
          error.config.headers.Authorization = `Bearer ${data.access_token}`
          return api.request(error.config)
        } catch (refreshError) {
          // Refresh failed, redirect to login
          clearAuthTokens()
          window.location.href = '/login'
        }
      } else {
        // No refresh token, redirect to login
        clearAuthTokens()
        window.location.href = '/login'
      }
    }
    return Promise.reject(error)
  }
)

// Auth API functions
export const authApi = {
  async getOAuthUrl(provider: 'google' | 'github', redirectUrl: string) {
    const { data } = await api.post('/api/v1/auth/oauth/signin', {
      provider,
      redirect_url: redirectUrl
    })
    return data
  },

  async handleOAuthCallback(code: string, state?: string) {
    const { data } = await api.post('/api/v1/auth/oauth/callback', {
      code,
      state
    })
    return data
  },

  async loginWithEmail(email: string, password: string) {
    const { data } = await api.post('/api/v1/auth/login', {
      email,
      password
    })
    return data
  },

  async signupWithEmail(email: string, password: string) {
    const { data } = await api.post('/api/v1/auth/signup', {
      email,
      password
    })
    return data
  },

  async getCurrentUser() {
    const { data } = await api.get('/api/v1/auth/me')
    return data
  },

  async logout() {
    await api.post('/api/v1/auth/logout')
  }
}

// User API functions
export const userApi = {
  async getUserProfile() {
    const { data } = await api.get('/api/v1/users/profile')
    return data
  },

  async updateUserProfile(updates: { full_name?: string; avatar_url?: string }) {
    const { data } = await api.put('/api/v1/users/profile', updates)
    return data
  },

  async getUserStats() {
    const { data } = await api.get('/api/v1/users/stats')
    return data
  },

  async getLinkedProviders() {
    const { data } = await api.get('/api/v1/users/providers')
    return data
  },

  async unlinkProvider(provider: string) {
    const { data } = await api.post(`/api/v1/users/providers/${provider}/unlink`)
    return data
  }
}

// Token management
export const setAuthTokens = (accessToken: string, refreshToken: string) => {
  Cookies.set('access_token', accessToken, { 
    expires: 7, // 7 days
    secure: process.env.NODE_ENV === 'production',
    sameSite: 'lax'
  })
  Cookies.set('refresh_token', refreshToken, { 
    expires: 30, // 30 days
    secure: process.env.NODE_ENV === 'production',
    sameSite: 'lax'
  })
}

export const clearAuthTokens = () => {
  Cookies.remove('access_token')
  Cookies.remove('refresh_token')
}

export const getAccessToken = () => Cookies.get('access_token')

export const refreshAuthToken = async (refreshToken: string) => {
  return api.post('/api/v1/auth/oauth/refresh', { refresh_token: refreshToken })
}

export default api
```

### 4. Authentication Context

```typescript
// contexts/AuthContext.tsx
'use client'

import React, { createContext, useContext, useEffect, useState } from 'react'
import { authApi, setAuthTokens, clearAuthTokens, getAccessToken } from '../lib/api'

interface User {
  id: string
  email: string
  full_name?: string
  avatar_url?: string
  provider?: string
  credits?: number
}

interface AuthContextType {
  user: User | null
  loading: boolean
  login: (email: string, password: string) => Promise<void>
  signup: (email: string, password: string) => Promise<void>
  loginWithOAuth: (provider: 'google' | 'github') => Promise<void>
  logout: () => Promise<void>
  refreshUser: () => Promise<void>
}

const AuthContext = createContext<AuthContextType | undefined>(undefined)

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [user, setUser] = useState<User | null>(null)
  const [loading, setLoading] = useState(true)

  // Check for existing session on mount
  useEffect(() => {
    checkAuthStatus()
  }, [])

  const checkAuthStatus = async () => {
    try {
      const token = getAccessToken()
      if (token) {
        const userData = await authApi.getCurrentUser()
        setUser(userData)
      }
    } catch (error) {
      console.error('Auth check failed:', error)
      clearAuthTokens()
    } finally {
      setLoading(false)
    }
  }

  const login = async (email: string, password: string) => {
    try {
      const data = await authApi.loginWithEmail(email, password)
      setAuthTokens(data.access_token, data.refresh_token)
      setUser(data.user)
    } catch (error) {
      console.error('Login failed:', error)
      throw error
    }
  }

  const signup = async (email: string, password: string) => {
    try {
      const data = await authApi.signupWithEmail(email, password)
      setAuthTokens(data.access_token, data.refresh_token)
      setUser(data.user)
    } catch (error) {
      console.error('Signup failed:', error)
      throw error
    }
  }

  const loginWithOAuth = async (provider: 'google' | 'github') => {
    try {
      const redirectUrl = `${window.location.origin}/auth/callback`
      const { url } = await authApi.getOAuthUrl(provider, redirectUrl)
      
      // Redirect to OAuth provider
      window.location.href = url
    } catch (error) {
      console.error('OAuth login failed:', error)
      throw error
    }
  }

  const logout = async () => {
    try {
      await authApi.logout()
    } catch (error) {
      console.error('Logout failed:', error)
    } finally {
      clearAuthTokens()
      setUser(null)
    }
  }

  const refreshUser = async () => {
    try {
      const userData = await authApi.getCurrentUser()
      setUser(userData)
    } catch (error) {
      console.error('Failed to refresh user:', error)
    }
  }

  const value = {
    user,
    loading,
    login,
    signup,
    loginWithOAuth,
    logout,
    refreshUser
  }

  return (
    <AuthContext.Provider value={value}>
      {children}
    </AuthContext.Provider>
  )
}

export function useAuth() {
  const context = useContext(AuthContext)
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider')
  }
  return context
}
```

### 5. OAuth Login Components

```typescript
// components/auth/OAuthButtons.tsx
'use client'

import { useState } from 'react'
import { useAuth } from '../../contexts/AuthContext'

export function OAuthButtons() {
  const { loginWithOAuth } = useAuth()
  const [loading, setLoading] = useState<string | null>(null)

  const handleOAuthLogin = async (provider: 'google' | 'github') => {
    try {
      setLoading(provider)
      await loginWithOAuth(provider)
    } catch (error) {
      console.error(`${provider} login failed:`, error)
      alert(`Failed to login with ${provider}. Please try again.`)
    } finally {
      setLoading(null)
    }
  }

  return (
    <div className="space-y-3">
      <button
        onClick={() => handleOAuthLogin('google')}
        disabled={loading === 'google'}
        className="w-full flex items-center justify-center px-4 py-3 border border-gray-300 rounded-lg shadow-sm text-sm font-medium text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 disabled:opacity-50 disabled:cursor-not-allowed"
      >
        {loading === 'google' ? (
          <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-gray-900"></div>
        ) : (
          <>
            <GoogleIcon className="w-5 h-5 mr-3" />
            Continue with Google
          </>
        )}
      </button>

      <button
        onClick={() => handleOAuthLogin('github')}
        disabled={loading === 'github'}
        className="w-full flex items-center justify-center px-4 py-3 border border-gray-300 rounded-lg shadow-sm text-sm font-medium text-white bg-gray-800 hover:bg-gray-900 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-gray-500 disabled:opacity-50 disabled:cursor-not-allowed"
      >
        {loading === 'github' ? (
          <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-white"></div>
        ) : (
          <>
            <GitHubIcon className="w-5 h-5 mr-3" />
            Continue with GitHub
          </>
        )}
      </button>
    </div>
  )
}

// Icons
function GoogleIcon({ className }: { className?: string }) {
  return (
    <svg className={className} viewBox="0 0 24 24">
      <path
        fill="currentColor"
        d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z"
      />
      <path
        fill="currentColor"
        d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z"
      />
      <path
        fill="currentColor"
        d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z"
      />
      <path
        fill="currentColor"
        d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z"
      />
    </svg>
  )
}

function GitHubIcon({ className }: { className?: string }) {
  return (
    <svg className={className} fill="currentColor" viewBox="0 0 24 24">
      <path d="M12 0c-6.626 0-12 5.373-12 12 0 5.302 3.438 9.8 8.207 11.387.599.111.793-.261.793-.577v-2.234c-3.338.726-4.033-1.416-4.033-1.416-.546-1.387-1.333-1.756-1.333-1.756-1.089-.745.083-.729.083-.729 1.205.084 1.839 1.237 1.839 1.237 1.07 1.834 2.807 1.304 3.492.997.107-.775.418-1.305.762-1.604-2.665-.305-5.467-1.334-5.467-5.931 0-1.311.469-2.381 1.236-3.221-.124-.303-.535-1.524.117-3.176 0 0 1.008-.322 3.301 1.23.957-.266 1.983-.399 3.003-.404 1.02.005 2.047.138 3.006.404 2.291-1.552 3.297-1.23 3.297-1.23.653 1.653.242 2.874.118 3.176.77.84 1.235 1.911 1.235 3.221 0 4.609-2.807 5.624-5.479 5.921.43.372.823 1.102.823 2.222v3.293c0 .319.192.694.801.576 4.765-1.589 8.199-6.086 8.199-11.386 0-6.627-5.373-12-12-12z" />
    </svg>
  )
}
```

### 6. Login Page

```typescript
// app/login/page.tsx
'use client'

import { useState } from 'react'
import { useRouter } from 'next/navigation'
import { useAuth } from '../../contexts/AuthContext'
import { OAuthButtons } from '../../components/auth/OAuthButtons'

export default function LoginPage() {
  const { login } = useAuth()
  const router = useRouter()
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setError('')
    setLoading(true)

    try {
      await login(email, password)
      router.push('/dashboard')
    } catch (error: any) {
      setError(error.response?.data?.detail || 'Login failed. Please try again.')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-50 py-12 px-4 sm:px-6 lg:px-8">
      <div className="max-w-md w-full space-y-8">
        <div>
          <h2 className="mt-6 text-center text-3xl font-extrabold text-gray-900">
            Sign in to LogoKraft
          </h2>
          <p className="mt-2 text-center text-sm text-gray-600">
            Create AI-powered logos in seconds
          </p>
        </div>

        <div className="mt-8 space-y-6">
          {/* OAuth Buttons */}
          <OAuthButtons />

          {/* Divider */}
          <div className="relative">
            <div className="absolute inset-0 flex items-center">
              <div className="w-full border-t border-gray-300" />
            </div>
            <div className="relative flex justify-center text-sm">
              <span className="px-2 bg-gray-50 text-gray-500">Or continue with email</span>
            </div>
          </div>

          {/* Email/Password Form */}
          <form className="space-y-6" onSubmit={handleSubmit}>
            {error && (
              <div className="rounded-md bg-red-50 p-4">
                <div className="text-sm text-red-700">{error}</div>
              </div>
            )}

            <div>
              <label htmlFor="email" className="block text-sm font-medium text-gray-700">
                Email address
              </label>
              <input
                id="email"
                name="email"
                type="email"
                autoComplete="email"
                required
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                className="mt-1 appearance-none relative block w-full px-3 py-2 border border-gray-300 placeholder-gray-500 text-gray-900 rounded-md focus:outline-none focus:ring-blue-500 focus:border-blue-500 focus:z-10 sm:text-sm"
                placeholder="Enter your email"
              />
            </div>

            <div>
              <label htmlFor="password" className="block text-sm font-medium text-gray-700">
                Password
              </label>
              <input
                id="password"
                name="password"
                type="password"
                autoComplete="current-password"
                required
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                className="mt-1 appearance-none relative block w-full px-3 py-2 border border-gray-300 placeholder-gray-500 text-gray-900 rounded-md focus:outline-none focus:ring-blue-500 focus:border-blue-500 focus:z-10 sm:text-sm"
                placeholder="Enter your password"
              />
            </div>

            <button
              type="submit"
              disabled={loading}
              className="group relative w-full flex justify-center py-2 px-4 border border-transparent text-sm font-medium rounded-md text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {loading ? (
                <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-white"></div>
              ) : (
                'Sign in'
              )}
            </button>

            <div className="text-center">
              <p className="text-sm text-gray-600">
                Don't have an account?{' '}
                <a href="/signup" className="font-medium text-blue-600 hover:text-blue-500">
                  Sign up
                </a>
              </p>
            </div>
          </form>
        </div>
      </div>
    </div>
  )
}
```

### 7. OAuth Callback Handler

```typescript
// app/auth/callback/page.tsx
'use client'

import { useEffect, useState } from 'react'
import { useRouter, useSearchParams } from 'next/navigation'
import { authApi, setAuthTokens } from '../../../lib/api'

export default function AuthCallback() {
  const router = useRouter()
  const searchParams = useSearchParams()
  const [status, setStatus] = useState<'processing' | 'success' | 'error'>('processing')
  const [error, setError] = useState('')

  useEffect(() => {
    const handleCallback = async () => {
      try {
        const code = searchParams.get('code')
        const state = searchParams.get('state')
        const error = searchParams.get('error')

        if (error) {
          throw new Error(`OAuth error: ${error}`)
        }

        if (!code) {
          throw new Error('Authorization code not found')
        }

        // Exchange code for tokens
        const data = await authApi.handleOAuthCallback(code, state || undefined)

        // Store tokens
        setAuthTokens(data.access_token, data.refresh_token)

        setStatus('success')

        // Redirect to dashboard after brief success message
        setTimeout(() => {
          router.push('/dashboard')
        }, 2000)

      } catch (error: any) {
        console.error('OAuth callback error:', error)
        setError(error.message || 'Authentication failed')
        setStatus('error')

        // Redirect to login after showing error
        setTimeout(() => {
          router.push('/login?error=oauth_failed')
        }, 3000)
      }
    }

    handleCallback()
  }, [searchParams, router])

  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-50">
      <div className="max-w-md w-full text-center">
        {status === 'processing' && (
          <div>
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto"></div>
            <h2 className="mt-4 text-xl font-semibold text-gray-900">
              Completing authentication...
            </h2>
            <p className="mt-2 text-gray-600">Please wait while we sign you in.</p>
          </div>
        )}

        {status === 'success' && (
          <div>
            <div className="mx-auto flex items-center justify-center h-12 w-12 rounded-full bg-green-100">
              <svg
                className="h-6 w-6 text-green-600"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M5 13l4 4L19 7"
                />
              </svg>
            </div>
            <h2 className="mt-4 text-xl font-semibold text-gray-900">
              Authentication successful!
            </h2>
            <p className="mt-2 text-gray-600">Redirecting to your dashboard...</p>
          </div>
        )}

        {status === 'error' && (
          <div>
            <div className="mx-auto flex items-center justify-center h-12 w-12 rounded-full bg-red-100">
              <svg
                className="h-6 w-6 text-red-600"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M6 18L18 6M6 6l12 12"
                />
              </svg>
            </div>
            <h2 className="mt-4 text-xl font-semibold text-gray-900">
              Authentication failed
            </h2>
            <p className="mt-2 text-gray-600">{error}</p>
            <p className="mt-4 text-sm text-gray-500">
              Redirecting back to login...
            </p>
          </div>
        )}
      </div>
    </div>
  )
}
```

### 8. User Profile with OAuth Management

```typescript
// components/profile/UserProfile.tsx
'use client'

import { useState, useEffect } from 'react'
import { useAuth } from '../../contexts/AuthContext'
import { userApi } from '../../lib/api'

interface UserProfile {
  id: string
  email: string
  full_name?: string
  avatar_url?: string
  provider: string
  credits: number
  providers: Array<{
    provider: string
    created_at: string
    last_sign_in_at: string
  }>
}

export function UserProfile() {
  const { user, refreshUser } = useAuth()
  const [profile, setProfile] = useState<UserProfile | null>(null)
  const [loading, setLoading] = useState(true)
  const [updating, setUpdating] = useState(false)
  const [formData, setFormData] = useState({
    full_name: '',
    avatar_url: ''
  })

  useEffect(() => {
    loadProfile()
  }, [])

  const loadProfile = async () => {
    try {
      const profileData = await userApi.getUserProfile()
      setProfile(profileData)
      setFormData({
        full_name: profileData.full_name || '',
        avatar_url: profileData.avatar_url || ''
      })
    } catch (error) {
      console.error('Failed to load profile:', error)
    } finally {
      setLoading(false)
    }
  }

  const handleUpdateProfile = async (e: React.FormEvent) => {
    e.preventDefault()
    setUpdating(true)

    try {
      await userApi.updateUserProfile(formData)
      await loadProfile()
      await refreshUser()
      alert('Profile updated successfully!')
    } catch (error) {
      console.error('Failed to update profile:', error)
      alert('Failed to update profile. Please try again.')
    } finally {
      setUpdating(false)
    }
  }

  const handleUnlinkProvider = async (provider: string) => {
    if (profile?.providers.length === 1) {
      alert('You must have at least one authentication method linked.')
      return
    }

    if (!confirm(`Are you sure you want to unlink ${provider}?`)) {
      return
    }

    try {
      await userApi.unlinkProvider(provider)
      await loadProfile()
      alert(`Successfully unlinked ${provider}`)
    } catch (error) {
      console.error('Failed to unlink provider:', error)
      alert('Failed to unlink provider. Please try again.')
    }
  }

  if (loading) {
    return (
      <div className="animate-pulse">
        <div className="h-8 bg-gray-200 rounded w-1/4 mb-4"></div>
        <div className="h-4 bg-gray-200 rounded w-1/2 mb-2"></div>
        <div className="h-4 bg-gray-200 rounded w-1/3"></div>
      </div>
    )
  }

  if (!profile) {
    return <div>Failed to load profile</div>
  }

  return (
    <div className="max-w-2xl mx-auto space-y-8">
      {/* Profile Header */}
      <div className="bg-white shadow rounded-lg p-6">
        <div className="flex items-center space-x-4">
          {profile.avatar_url ? (
            <img
              src={profile.avatar_url}
              alt="Profile"
              className="h-16 w-16 rounded-full"
            />
          ) : (
            <div className="h-16 w-16 rounded-full bg-gray-300 flex items-center justify-center">
              <span className="text-xl font-semibold text-gray-600">
                {profile.full_name?.charAt(0) || profile.email.charAt(0)}
              </span>
            </div>
          )}
          <div>
            <h2 className="text-2xl font-bold text-gray-900">
              {profile.full_name || 'No name set'}
            </h2>
            <p className="text-gray-600">{profile.email}</p>
            <p className="text-sm text-gray-500">
              Primary provider: {profile.provider}
            </p>
          </div>
        </div>
      </div>

      {/* Update Profile Form */}
      <div className="bg-white shadow rounded-lg p-6">
        <h3 className="text-lg font-medium text-gray-900 mb-4">
          Update Profile
        </h3>
        <form onSubmit={handleUpdateProfile} className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700">
              Full Name
            </label>
            <input
              type="text"
              value={formData.full_name}
              onChange={(e) => setFormData(prev => ({ ...prev, full_name: e.target.value }))}
              className="mt-1 block w-full border-gray-300 rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500"
              placeholder="Enter your full name"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700">
              Avatar URL
            </label>
            <input
              type="url"
              value={formData.avatar_url}
              onChange={(e) => setFormData(prev => ({ ...prev, avatar_url: e.target.value }))}
              className="mt-1 block w-full border-gray-300 rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500"
              placeholder="https://example.com/avatar.jpg"
            />
          </div>

          <button
            type="submit"
            disabled={updating}
            className="inline-flex justify-center py-2 px-4 border border-transparent shadow-sm text-sm font-medium rounded-md text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 disabled:opacity-50"
          >
            {updating ? 'Updating...' : 'Update Profile'}
          </button>
        </form>
      </div>

      {/* Linked Providers */}
      <div className="bg-white shadow rounded-lg p-6">
        <h3 className="text-lg font-medium text-gray-900 mb-4">
          Linked Accounts
        </h3>
        <div className="space-y-3">
          {profile.providers.map((provider) => (
            <div
              key={provider.provider}
              className="flex items-center justify-between p-3 border border-gray-200 rounded-lg"
            >
              <div className="flex items-center space-x-3">
                <div className="flex-shrink-0">
                  {provider.provider === 'google' && <GoogleIcon className="h-6 w-6" />}
                  {provider.provider === 'github' && <GitHubIcon className="h-6 w-6" />}
                  {provider.provider === 'email' && (
                    <div className="h-6 w-6 bg-gray-400 rounded-full flex items-center justify-center">
                      <span className="text-xs text-white">@</span>
                    </div>
                  )}
                </div>
                <div>
                  <p className="text-sm font-medium text-gray-900">
                    {provider.provider.charAt(0).toUpperCase() + provider.provider.slice(1)}
                  </p>
                  <p className="text-xs text-gray-500">
                    Last used: {new Date(provider.last_sign_in_at).toLocaleDateString()}
                  </p>
                </div>
              </div>
              {profile.providers.length > 1 && provider.provider !== 'email' && (
                <button
                  onClick={() => handleUnlinkProvider(provider.provider)}
                  className="text-red-600 hover:text-red-800 text-sm font-medium"
                >
                  Unlink
                </button>
              )}
            </div>
          ))}
        </div>
      </div>

      {/* Account Stats */}
      <div className="bg-white shadow rounded-lg p-6">
        <h3 className="text-lg font-medium text-gray-900 mb-4">
          Account Overview
        </h3>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div className="text-center">
            <p className="text-2xl font-bold text-blue-600">{profile.credits}</p>
            <p className="text-sm text-gray-600">Credits Remaining</p>
          </div>
          <div className="text-center">
            <p className="text-2xl font-bold text-green-600">
              {new Date(profile.providers[0]?.created_at).toLocaleDateString()}
            </p>
            <p className="text-sm text-gray-600">Member Since</p>
          </div>
          <div className="text-center">
            <p className="text-2xl font-bold text-purple-600">{profile.providers.length}</p>
            <p className="text-sm text-gray-600">Linked Accounts</p>
          </div>
        </div>
      </div>
    </div>
  )
}
```

## 🔧 Usage Instructions

1. **Setup Supabase OAuth** (follow OAUTH_SETUP_GUIDE.md)
2. **Install the frontend** using the code above
3. **Configure environment variables** in `.env.local`
4. **Test the OAuth flow**:
   - Click "Continue with Google/GitHub"
   - Complete OAuth authorization
   - Get redirected back with user data
   - Access user profile and management features

## 🚀 Key Features

✅ **Complete OAuth Integration** - Google & GitHub
✅ **Token Management** - Automatic refresh and secure storage
✅ **User Profile Management** - Update name, avatar, and view linked accounts
✅ **Provider Management** - Link/unlink multiple OAuth providers
✅ **Error Handling** - Comprehensive error states and user feedback
✅ **TypeScript** - Full type safety
✅ **Responsive Design** - Works on all devices
✅ **Production Ready** - Secure, scalable, and maintainable

This provides everything you need for a complete OAuth implementation with Google and GitHub for LogoKraft!
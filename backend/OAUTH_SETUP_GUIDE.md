# Complete OAuth Setup Guide for LogoKraft

## 🚀 Overview
This guide covers setting up Google and GitHub OAuth authentication for LogoKraft using Supabase Auth.

## 📋 Prerequisites
- Supabase project with Auth enabled
- Access to Google Cloud Console
- Access to GitHub Developer Settings
- Domain where your app will be hosted

---

## 🟦 Google OAuth Setup

### Step 1: Create Google Cloud Project

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Click "Select a project" → "New Project"
3. Enter project name: `LogoKraft-OAuth`
4. Click "Create"

### Step 2: Enable Google+ API

1. In Google Cloud Console, go to "APIs & Services" → "Library"
2. Search for "Google+ API"
3. Click "Google+ API" and click "Enable"
4. Also enable "People API" for profile information

### Step 3: Configure OAuth Consent Screen

1. Go to "APIs & Services" → "OAuth consent screen"
2. Choose "External" for user type
3. Fill out the required fields:
   ```
   App name: LogoKraft
   User support email: your-email@domain.com
   App logo: (optional, upload your logo)
   Application homepage: https://your-domain.com
   Privacy policy: https://your-domain.com/privacy
   Terms of service: https://your-domain.com/terms
   ```
4. Add scopes:
   - `../auth/userinfo.email`
   - `../auth/userinfo.profile`
   - `openid`
5. Add test users (for development):
   - Add your test email addresses

### Step 4: Create OAuth Credentials

1. Go to "APIs & Services" → "Credentials"
2. Click "Create Credentials" → "OAuth 2.0 Client IDs"
3. Application type: "Web application"
4. Name: `LogoKraft Web Client`
5. **Authorized JavaScript origins:**
   ```
   Development:
   http://localhost:3000
   
   Production:
   https://your-domain.com
   ```
6. **Authorized redirect URIs:**
   ```
   Development:
   https://your-supabase-project.supabase.co/auth/v1/callback
   
   Production:
   https://your-supabase-project.supabase.co/auth/v1/callback
   ```
7. Click "Create"
8. **Save the Client ID and Client Secret** - you'll need these for Supabase

### Step 5: Configure Supabase

1. Go to your Supabase Dashboard
2. Navigate to "Authentication" → "Providers"
3. Find "Google" and toggle it on
4. Enter your Google OAuth credentials:
   ```
   Client ID: your-google-client-id
   Client Secret: your-google-client-secret
   ```
5. Click "Save"

---

## 🟦 GitHub OAuth Setup

### Step 1: Create GitHub OAuth App

1. Go to [GitHub Developer Settings](https://github.com/settings/developers)
2. Click "OAuth Apps" → "New OAuth App"
3. Fill out the form:
   ```
   Application name: LogoKraft
   Homepage URL: https://your-domain.com
   Application description: AI-powered logo generation platform
   ```
4. **Authorization callback URL:**
   ```
   https://your-supabase-project.supabase.co/auth/v1/callback
   ```
5. Click "Register application"

### Step 2: Get Client Credentials

1. After creating the app, you'll see the "Client ID"
2. Click "Generate a new client secret"
3. **Save both the Client ID and Client Secret**

### Step 3: Configure Supabase

1. Go to your Supabase Dashboard
2. Navigate to "Authentication" → "Providers"
3. Find "GitHub" and toggle it on
4. Enter your GitHub OAuth credentials:
   ```
   Client ID: your-github-client-id
   Client Secret: your-github-client-secret
   ```
5. Click "Save"

---

## 🔧 Supabase Configuration

### Environment Variables

Add these to your Supabase project settings and your local `.env` file:

```bash
# In your .env file (backend)
SUPABASE_URL=https://your-project-ref.supabase.co
SUPABASE_ANON_KEY=your_anon_public_key_here
SUPABASE_SERVICE_KEY=your_service_role_key_here

# OAuth Settings (automatically handled by Supabase)
# No additional environment variables needed for OAuth
```

### Site URL Configuration

1. In Supabase Dashboard, go to "Authentication" → "URL Configuration"
2. Set your site URLs:
   ```
   Site URL: https://your-domain.com
   Additional redirect URLs:
   - http://localhost:3000 (for development)
   - https://your-domain.com/auth/callback
   ```

---

## 🎯 Frontend Integration Examples

### React.js with Supabase

```typescript
// Install dependencies
npm install @supabase/supabase-js

// lib/supabase.ts
import { createClient } from '@supabase/supabase-js'

const supabaseUrl = process.env.NEXT_PUBLIC_SUPABASE_URL!
const supabaseAnonKey = process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY!

export const supabase = createClient(supabaseUrl, supabaseAnonKey)

// components/AuthButtons.tsx
import { supabase } from '../lib/supabase'

export function AuthButtons() {
  const signInWithGoogle = async () => {
    const { data, error } = await supabase.auth.signInWithOAuth({
      provider: 'google',
      options: {
        redirectTo: `${window.location.origin}/auth/callback`
      }
    })
    if (error) console.error('Error:', error)
  }

  const signInWithGitHub = async () => {
    const { data, error } = await supabase.auth.signInWithOAuth({
      provider: 'github',
      options: {
        redirectTo: `${window.location.origin}/auth/callback`
      }
    })
    if (error) console.error('Error:', error)
  }

  return (
    <div className="space-y-4">
      <button 
        onClick={signInWithGoogle}
        className="w-full flex items-center justify-center px-4 py-2 border border-gray-300 rounded-md shadow-sm text-sm font-medium text-gray-700 bg-white hover:bg-gray-50"
      >
        <svg className="w-5 h-5 mr-2" viewBox="0 0 24 24">
          {/* Google Icon SVG */}
        </svg>
        Continue with Google
      </button>
      
      <button 
        onClick={signInWithGitHub}
        className="w-full flex items-center justify-center px-4 py-2 border border-gray-300 rounded-md shadow-sm text-sm font-medium text-white bg-gray-800 hover:bg-gray-900"
      >
        <svg className="w-5 h-5 mr-2" fill="currentColor" viewBox="0 0 24 24">
          {/* GitHub Icon SVG */}
        </svg>
        Continue with GitHub
      </button>
    </div>
  )
}

// pages/auth/callback.tsx (Next.js)
import { useEffect } from 'react'
import { useRouter } from 'next/router'
import { supabase } from '../../lib/supabase'

export default function AuthCallback() {
  const router = useRouter()

  useEffect(() => {
    const handleAuthCallback = async () => {
      const { data, error } = await supabase.auth.getSession()
      
      if (error) {
        console.error('Auth error:', error)
        router.push('/login?error=auth_failed')
        return
      }

      if (data.session) {
        // User is authenticated, redirect to dashboard
        router.push('/dashboard')
      } else {
        // No session, redirect to login
        router.push('/login')
      }
    }

    handleAuthCallback()
  }, [router])

  return (
    <div className="flex items-center justify-center min-h-screen">
      <div className="text-center">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600 mx-auto"></div>
        <p className="mt-4 text-gray-600">Completing authentication...</p>
      </div>
    </div>
  )
}
```

### Alternative: Using Your Custom API

```typescript
// If you prefer to use your custom backend API instead of direct Supabase

// lib/api.ts
const API_BASE = process.env.NEXT_PUBLIC_API_URL

export const authApi = {
  async getOAuthUrl(provider: 'google' | 'github', redirectUrl: string) {
    const response = await fetch(`${API_BASE}/api/v1/auth/oauth/signin`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ provider, redirect_url: redirectUrl })
    })
    return response.json()
  },

  async handleOAuthCallback(code: string, state?: string) {
    const response = await fetch(`${API_BASE}/api/v1/auth/oauth/callback`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ code, state })
    })
    return response.json()
  }
}

// components/AuthButtons.tsx
import { authApi } from '../lib/api'

export function AuthButtons() {
  const handleOAuth = async (provider: 'google' | 'github') => {
    try {
      const redirectUrl = `${window.location.origin}/auth/callback`
      const { url } = await authApi.getOAuthUrl(provider, redirectUrl)
      window.location.href = url
    } catch (error) {
      console.error('OAuth error:', error)
    }
  }

  return (
    <div className="space-y-4">
      <button onClick={() => handleOAuth('google')}>
        Continue with Google
      </button>
      <button onClick={() => handleOAuth('github')}>
        Continue with GitHub
      </button>
    </div>
  )
}
```

---

## 🔍 Testing Your OAuth Setup

### Test Checklist

1. **Google OAuth Test:**
   - [ ] Click "Continue with Google" button
   - [ ] Redirected to Google consent screen
   - [ ] Can authorize the application
   - [ ] Redirected back to your app with user data
   - [ ] User profile shows Google avatar and name

2. **GitHub OAuth Test:**
   - [ ] Click "Continue with GitHub" button
   - [ ] Redirected to GitHub authorization page
   - [ ] Can authorize the application
   - [ ] Redirected back to your app with user data
   - [ ] User profile shows GitHub avatar and username

3. **Backend API Test:**
   ```bash
   # Test OAuth URL generation
   curl -X POST http://localhost:8000/api/v1/auth/oauth/signin \
     -H "Content-Type: application/json" \
     -d '{"provider": "google", "redirect_url": "http://localhost:3000/auth/callback"}'
   
   # Should return: {"url": "https://accounts.google.com/oauth/authorize?...", "state": "..."}
   ```

---

## 🚨 Troubleshooting

### Common Issues

1. **"redirect_uri_mismatch" Error**
   - Check that your redirect URI in Google Console exactly matches Supabase
   - Ensure no trailing slashes or typos
   - URI: `https://your-project.supabase.co/auth/v1/callback`

2. **"Application not found" Error**
   - Verify your Client ID and Client Secret in Supabase
   - Check that OAuth provider is enabled in Supabase

3. **"Unauthorized" Error**
   - Add your domain to authorized origins in Google Console
   - Check that your app is not in "Testing" mode for production use

4. **User data not showing**
   - Verify scopes include email and profile
   - Check that your backend properly extracts user metadata

### Debug Mode

Enable debug logging in your backend:

```python
# In your main.py or logging config
logging.getLogger('app.services.oauth_service').setLevel(logging.DEBUG)
```

---

## 🔐 Security Best Practices

1. **Environment Variables:**
   - Never commit OAuth secrets to version control
   - Use different OAuth apps for development and production
   - Rotate secrets regularly

2. **HTTPS Only:**
   - Always use HTTPS in production
   - Configure OAuth apps to only allow HTTPS redirects

3. **CSRF Protection:**
   - Always use and validate the `state` parameter
   - Implement proper session management

4. **Scope Minimization:**
   - Only request necessary OAuth scopes
   - Regularly audit granted permissions

---

## 📚 Additional Resources

- [Supabase Auth Documentation](https://supabase.com/docs/guides/auth)
- [Google OAuth 2.0 Documentation](https://developers.google.com/identity/protocols/oauth2)
- [GitHub OAuth Apps Documentation](https://docs.github.com/en/developers/apps/building-oauth-apps)

---

**Next Steps:**
1. Set up your OAuth applications following this guide
2. Test the authentication flow in development
3. Deploy to production with proper domain configuration
4. Monitor OAuth usage and errors in your application logs
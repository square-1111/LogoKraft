# LogoKraft Frontend Design Specification

## 🎯 Executive Summary

This document provides a comprehensive frontend implementation plan for LogoKraft based on detailed backend analysis. The frontend will support the complete user journey from authentication through AI logo generation to brand kit purchase.

**Core User Flow:**
Authentication → Project Creation → AI Generation (15 concepts) → Logo Selection → Refinement (5 credits) → Brand Kit Purchase ($29)

## 📊 Backend Analysis Summary

### API Endpoints Mapped

**Authentication:**
- `POST /api/v1/auth/signup` - User registration
- `POST /api/v1/auth/login` - User authentication  
- `GET /api/v1/auth/me` - Current user info

**Projects:**
- `POST /api/v1/projects` - Create project (triggers AI generation)
- `GET /api/v1/projects/{id}` - Project details
- `GET /api/v1/projects/{id}/assets` - Generated logos
- `GET /api/v1/projects/{id}/stream` - Real-time SSE updates
- `GET /api/v1/projects/credits` - Credit balance

**Refinement:**
- `POST /api/v1/assets/{id}/simple-refine` - Generate 5 variations (costs 5 credits)

**Brand Kit:**
- `POST /api/v1/brand-kit/purchase` - Purchase $29 brand kit
- `GET /api/v1/brand-kit/orders/{id}` - Order status
- `GET /api/v1/brand-kit/orders/{id}/stream` - Generation progress

**Payments:**
- `POST /api/v1/stripe/create-payment-intent` - Payment setup
- `POST /api/v1/stripe/create-checkout-session` - Hosted checkout
- `POST /api/v1/stripe/webhook` - Payment confirmations
- `POST /api/v1/stripe/refund/{order_id}` - Process refunds

### Data Models

**Projects:**
```typescript
interface Project {
  id: string;
  project_name: string;
  brief_data: {
    company_name: string;
    industry: string;
    description?: string;
  };
  inspiration_image_url?: string;
  created_at: string;
  updated_at: string;
}
```

**Assets:**
```typescript
interface Asset {
  id: string;
  project_id: string;
  asset_type: 'logo_concept' | 'simple_refinement';
  status: 'pending' | 'generating' | 'completed' | 'failed';
  asset_url?: string;
  generation_prompt: string;
  parent_asset_id?: string;
  created_at: string;
  updated_at: string;
}
```

**Brand Kit Orders:**
```typescript
interface BrandKitOrder {
  id: string;
  user_id: string;
  project_id: string;
  selected_asset_id: string;
  order_status: 'pending' | 'processing' | 'completed' | 'failed' | 'refunded';
  payment_amount: number;
  payment_status: 'pending' | 'completed' | 'failed';
  payment_reference: string;
  components: {
    business_cards?: string[];
    website_mockup?: string;
    social_headers?: string[];
    tshirt_design?: string;
    animated_logo?: { gif: string; mp4: string };
  };
}
```

## 📱 Frontend Architecture

### Page Structure (9 Core Pages)

#### 1. Authentication Pages
**Routes:** `/login`, `/signup`, `/forgot-password`

**Features:**
- Simple email/password forms
- JWT token management
- Auto-redirect after authentication
- Error handling for Supabase auth errors

**Components:**
- `LoginForm.tsx`
- `SignupForm.tsx`
- `AuthLayout.tsx`

#### 2. Dashboard Home
**Route:** `/dashboard`

**Layout:**
```
┌─────────────────────────────────────────────────────────┐
│ LogoKraft | Projects | Credits: 95 | [User Menu]       │
├─────────────────────────────────────────────────────────┤
│                                                         │
│  Recent Projects                    [+ New Project]     │
│  ┌───────┐ ┌───────┐ ┌───────┐ ┌───────┐              │
│  │ Proj1 │ │ Proj2 │ │ Proj3 │ │ Proj4 │              │
│  │       │ │       │ │       │ │ +New  │              │
│  └───────┘ └───────┘ └───────┘ └───────┘              │
│                                                         │
│  Usage Overview                                         │
│  ┌─────────────────────────────────────────────────┐   │
│  │ Logos Generated: 45  Credits Used: 25          │   │
│  │ Brand Kits: 2        Total Projects: 8         │   │
│  └─────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────┘
```

**Components:**
- `ProjectGrid.tsx`
- `CreditBalance.tsx`
- `UsageStats.tsx`
- `QuickActions.tsx`

#### 3. Project Creation
**Route:** `/projects/new`

**Form Fields:**
- Company name (required, 1-100 chars)
- Industry dropdown (required)
- Description (optional, max 500 chars)
- Inspiration image (optional, max 5MB, JPEG/PNG)

**API Integration:**
- `POST /api/v1/projects` with FormData
- Immediate redirect to generation view

#### 4. Generation Progress
**Route:** `/projects/{id}/generating`

**Features:**
- Real-time SSE connection to `/api/v1/projects/{id}/stream`
- Progress bars for 3 studios (Helios, '78, Apex)
- Live thumbnail grid as concepts complete
- Auto-redirect when all 15 logos ready

**SSE Message Types:**
```typescript
interface StreamMessage {
  type: 'connection' | 'asset_update' | 'generation_complete' | 'error';
  data: any;
  timestamp: string;
}
```

#### 5. Logo Selection
**Route:** `/projects/{id}/select`

**Features:**
- Grid of 15 generated concepts
- Single selection with preview
- Studio organization (5 logos per studio)
- Continue to refinement or brand kit

#### 6. Logo Refinement
**Route:** `/projects/{id}/refine/{assetId}`

**Features:**
- Selected logo display
- Optional text prompt (500 char limit)
- "Generate 5 Variations (5 Credits)" button
- Real-time generation progress
- Selection from variations

#### 7. Brand Kit Preview
**Route:** `/projects/{id}/brand-kit`

**Brand Kit Components ($29):**
- Business Cards (2 contrast versions)
- Website Mockup (homepage design)
- Social Media Headers (4 platforms)
- T-shirt Mockup (apparel design)
- Animated Logo (GIF + MP4)

**Payment Integration:**
- Stripe Elements for secure payment
- Component preview mockups
- Order tracking after purchase

#### 8. Project Library
**Route:** `/projects`

**Features:**
- All user projects with status badges
- Filter by status and industry
- Search functionality
- Quick access to refinement/brand kit

#### 9. Account Management
**Route:** `/account`

**Features:**
- Credit balance and purchase
- Transaction history
- Profile settings
- Billing information

## 🔧 Technical Implementation

### Recommended Tech Stack

```bash
# Next.js 14 with TypeScript
npx create-next-app@latest logokraft-frontend --typescript --tailwind --app

# Core Dependencies
npm install @tanstack/react-query axios zustand
npm install @stripe/stripe-js @stripe/react-stripe-js
npm install react-hook-form @hookform/resolvers zod
npm install framer-motion lucide-react
npm install @headlessui/react @heroicons/react
```

### Project Structure

```
src/
├── app/                    # Next.js App Router
│   ├── (auth)/
│   │   ├── login/page.tsx
│   │   └── signup/page.tsx
│   ├── dashboard/page.tsx
│   ├── projects/
│   │   ├── new/page.tsx
│   │   └── [id]/
│   │       ├── page.tsx
│   │       ├── generating/page.tsx
│   │       ├── select/page.tsx
│   │       └── refine/[assetId]/page.tsx
│   └── account/page.tsx
├── components/
│   ├── layout/
│   │   ├── Header.tsx
│   │   ├── Sidebar.tsx
│   │   └── Layout.tsx
│   ├── auth/
│   │   ├── LoginForm.tsx
│   │   └── SignupForm.tsx
│   ├── projects/
│   │   ├── ProjectForm.tsx
│   │   ├── ProjectCard.tsx
│   │   └── ProjectGrid.tsx
│   ├── generation/
│   │   ├── ProgressView.tsx
│   │   ├── StudioProgress.tsx
│   │   └── AssetThumbnail.tsx
│   ├── refinement/
│   │   ├── AssetSelector.tsx
│   │   ├── RefinementForm.tsx
│   │   └── VariationGrid.tsx
│   ├── brand-kit/
│   │   ├── BrandKitPreview.tsx
│   │   ├── ComponentShowcase.tsx
│   │   └── PurchaseButton.tsx
│   └── common/
│       ├── Button.tsx
│       ├── Card.tsx
│       ├── Modal.tsx
│       └── Loading.tsx
├── hooks/
│   ├── useAuth.ts
│   ├── useProjectProgress.ts
│   └── useCredits.ts
├── lib/
│   ├── api.ts
│   ├── auth.ts
│   └── stripe.ts
├── stores/
│   └── appStore.ts
└── types/
    ├── api.ts
    └── stripe.ts
```

### Core Implementation Examples

#### Authentication Service

```typescript
// lib/auth.ts
export class AuthService {
  private baseURL = process.env.NEXT_PUBLIC_API_URL;

  async login(email: string, password: string) {
    const response = await fetch(`${this.baseURL}/api/v1/auth/login`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ email, password })
    });
    
    if (!response.ok) throw new Error('Login failed');
    
    const data = await response.json();
    
    // Store tokens securely
    localStorage.setItem('access_token', data.access_token);
    localStorage.setItem('refresh_token', data.refresh_token);
    
    return data;
  }

  getAuthHeaders() {
    const token = localStorage.getItem('access_token');
    return token ? { Authorization: `Bearer ${token}` } : {};
  }
}
```

#### Real-Time Progress Hook

```typescript
// hooks/useProjectProgress.ts
export function useProjectProgress(projectId: string) {
  const [status, setStatus] = useState<'connecting' | 'connected' | 'error'>('connecting');
  const [assets, setAssets] = useState<Asset[]>([]);
  const [studios, setStudios] = useState({
    helios: { completed: 0, total: 5 },
    seventyEight: { completed: 0, total: 5 },
    apex: { completed: 0, total: 5 }
  });

  useEffect(() => {
    const eventSource = new EventSource(
      `${API_URL}/api/v1/projects/${projectId}/stream`,
      {
        headers: {
          Authorization: `Bearer ${localStorage.getItem('access_token')}`
        }
      }
    );

    eventSource.onopen = () => setStatus('connected');
    
    eventSource.onmessage = (event) => {
      const message = JSON.parse(event.data);
      
      switch (message.type) {
        case 'asset_update':
          setAssets(prev => {
            const exists = prev.find(a => a.id === message.data.asset_id);
            if (exists) return prev;
            return [...prev, message.data];
          });
          break;
          
        case 'generation_complete':
          router.push(`/projects/${projectId}/select`);
          break;
      }
    };

    eventSource.onerror = () => setStatus('error');
    return () => eventSource.close();
  }, [projectId]);

  return { status, assets, studios };
}
```

#### Stripe Payment Component

```typescript
// components/brand-kit/PaymentForm.tsx
import { loadStripe } from '@stripe/stripe-js';
import { Elements, CardElement, useStripe, useElements } from '@stripe/react-stripe-js';

const stripePromise = loadStripe(process.env.NEXT_PUBLIC_STRIPE_PUBLISHABLE_KEY!);

export function BrandKitPurchase({ selectedAssetId }: { selectedAssetId: string }) {
  return (
    <Elements stripe={stripePromise}>
      <PaymentForm selectedAssetId={selectedAssetId} />
    </Elements>
  );
}

function PaymentForm({ selectedAssetId }: { selectedAssetId: string }) {
  const stripe = useStripe();
  const elements = useElements();
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!stripe || !elements) return;

    setLoading(true);

    // Create payment intent
    const response = await fetch('/api/v1/stripe/create-payment-intent', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        ...getAuthHeaders()
      },
      body: JSON.stringify({ selected_asset_id: selectedAssetId })
    });

    const { payment_intent } = await response.json();

    // Confirm payment
    const result = await stripe.confirmCardPayment(payment_intent.client_secret, {
      payment_method: {
        card: elements.getElement(CardElement)!
      }
    });

    if (result.error) {
      // Handle error
    } else {
      // Payment successful
      router.push(`/brand-kit/orders/${payment_intent.order_id}`);
    }

    setLoading(false);
  };

  return (
    <form onSubmit={handleSubmit}>
      <CardElement />
      <button type="submit" disabled={!stripe || loading}>
        {loading ? 'Processing...' : 'Purchase Brand Kit ($29)'}
      </button>
    </form>
  );
}
```

#### Global State Management

```typescript
// stores/appStore.ts
import { create } from 'zustand';

interface AppState {
  user: User | null;
  credits: number;
  currentProject: Project | null;
  
  // Actions
  setUser: (user: User | null) => void;
  setCredits: (credits: number) => void;
  updateCredits: (delta: number) => void;
  setCurrentProject: (project: Project | null) => void;
}

export const useAppStore = create<AppState>((set) => ({
  user: null,
  credits: 0,
  currentProject: null,
  
  setUser: (user) => set({ user }),
  setCredits: (credits) => set({ credits }),
  updateCredits: (delta) => set((state) => ({ 
    credits: state.credits + delta 
  })),
  setCurrentProject: (project) => set({ currentProject: project })
}));
```

## 🚀 Development Roadmap

### Phase 1: Foundation (Week 1-2)
**Setup & Authentication**
- [ ] Next.js project setup with TypeScript
- [ ] Authentication flow (login/signup)
- [ ] Route protection middleware
- [ ] Token management and refresh
- [ ] Header with navigation and credit display
- [ ] Responsive layout structure

### Phase 2: Core Features (Week 3-4)
**Project Creation & Generation**
- [ ] Project creation form with validation
- [ ] Image upload handling
- [ ] SSE connection for real-time updates
- [ ] Progress visualization
- [ ] Asset grid with live updates

### Phase 3: Advanced Features (Week 5-6)
**Selection & Refinement**
- [ ] Asset selection interface
- [ ] Refinement form and progress
- [ ] Credit system integration
- [ ] Stripe payment integration
- [ ] Brand kit component preview

### Phase 4: Polish (Week 7-8)
**Performance & UX**
- [ ] Image optimization
- [ ] Loading states and error handling
- [ ] Mobile responsiveness
- [ ] Unit tests for critical components
- [ ] E2E tests for main flows
- [ ] Production deployment setup

## 🎨 Design System

### Color Palette
```css
:root {
  /* Primary Colors */
  --primary: #6366F1;        /* Indigo */
  --primary-dark: #4F46E5;
  --secondary: #8B5CF6;      /* Purple */
  
  /* Status Colors */
  --success: #10B981;        /* Green */
  --warning: #F59E0B;        /* Amber */
  --error: #EF4444;          /* Red */
  
  /* Neutral Colors */
  --neutral-50: #F9FAFB;
  --neutral-100: #F3F4F6;
  --neutral-900: #111827;
  
  /* Spacing */
  --space-xs: 0.25rem;
  --space-sm: 0.5rem;
  --space-md: 1rem;
  --space-lg: 1.5rem;
  --space-xl: 2rem;
}
```

### Typography
- Primary Font: 'Inter' (body text)
- Display Font: 'Poppins' (headings)
- Font sizes: Tailwind default scale

### Component Standards
- Consistent button styles with loading states
- Card components with proper shadows
- Form inputs with validation styling
- Modal overlays with proper focus management

## 🧪 Testing Strategy

### Unit Tests
- Authentication service methods
- Form validation logic
- State management stores
- Utility functions

### Integration Tests
- API service calls
- Payment flow integration
- SSE connection handling
- Route protection

### E2E Tests (Cypress)
- Complete user registration flow
- Project creation and generation
- Logo selection and refinement
- Brand kit purchase flow

## 🚀 Performance Considerations

### Image Optimization
- Next.js Image component for all logo assets
- Progressive loading for asset grids
- Placeholder images during loading

### Bundle Optimization
- Code splitting for routes
- Dynamic imports for heavy components
- Tree shaking for unused code

### Caching Strategy
- React Query for API data caching
- SWR for real-time data
- LocalStorage for user preferences

## 🔒 Security Measures

### Authentication
- JWT token storage in localStorage
- Automatic token refresh
- Protected route middleware

### Input Validation
- Client-side validation with Zod schemas
- File upload restrictions
- XSS prevention

### Payment Security
- Stripe Elements for PCI compliance
- No card data stored locally
- Webhook signature verification

## 📱 Mobile Considerations

### Responsive Breakpoints
- Mobile: 0-640px
- Tablet: 641-1024px
- Desktop: 1025px+

### Mobile-Specific Features
- Touch-friendly button sizes
- Optimized image loading
- Simplified navigation

### Performance
- Reduced initial bundle size
- Lazy loading for non-critical components
- Optimized for 3G networks

## 🎯 Success Metrics

### Technical KPIs
- Page load time < 3 seconds
- First Contentful Paint < 1.5 seconds
- SSE connection success rate > 99%
- Payment completion rate > 95%

### User Experience KPIs
- Project creation completion rate
- Generation session completion rate
- Refinement usage rate
- Brand kit conversion rate

## 🚀 Additional Pages Analysis: Complete Frontend Architecture

Based on comprehensive Zen MCP analysis of LogoKraft's backend architecture, business model, and user lifecycle, **39 additional pages** are required beyond the 9 core pages, bringing the total to **48 pages** for a production-ready frontend.

### **Complete Page Inventory**

#### **Core Application Pages (9)**
✅ Authentication (login/signup)  
✅ Dashboard home  
✅ Project creation  
✅ Generation progress  
✅ Logo selection  
✅ Logo refinement  
✅ Brand kit preview/purchase  
✅ Project library  
✅ Account management  

#### **Additional Required Pages (39)**

### 🔥 **CRITICAL PRIORITY - Must-Have for Launch (14 pages)**

#### **User Lifecycle & Onboarding (5 pages)**
```
/welcome              - Post-signup welcome with tutorial
/verify-email         - Email verification landing page  
/reset-password       - Password reset form
/password-confirmed   - Reset confirmation page
/getting-started      - Interactive onboarding walkthrough
```

**API Integration:**
- Links to existing auth endpoints in `auth_routes.py`
- Handles email confirmation flow (line 138: "Email not confirmed")
- Guides users through first project creation

#### **Legal & Compliance (5 pages)**
```
/terms               - Terms of Service
/privacy             - Privacy Policy
/cookie-policy       - Cookie usage policy  
/refund-policy       - Refund terms for $29 brand kits
/dmca                - Copyright dispute handling
```

**Business Requirements:**
- Required for Stripe compliance and $29 brand kit sales
- GDPR compliance for international users
- Copyright protection for AI-generated logos
- Refund policy links to `/api/v1/stripe/refund/{order_id}` endpoint

#### **Error Handling (4 pages)**
```
/404                 - Custom page not found
/500                 - Server error page
/maintenance         - Planned maintenance mode
/payment-failed      - Payment processing errors with retry options
```

**Technical Integration:**
- Handles API error responses (400, 401, 404, 500 from backend)
- Payment failure recovery for Stripe integration
- Graceful degradation during AI generation failures

### 📈 **HIGH PRIORITY - Business Growth (13 pages)**

#### **Marketing & Conversion (6 pages)**
```
/                    - Marketing landing page (public, SEO-optimized)
/features            - Product features showcase (APEX-7, 15 concepts)
/pricing             - Credit packages and $29 brand kit pricing
/examples            - Logo portfolio gallery (showcase quality)
/how-it-works        - Process explanation (AI workflow)
/testimonials        - Customer success stories
```

**Business Impact:**
- Drive organic traffic and user acquisition
- Explain credit system and brand kit value proposition
- Showcase AI-generated logo quality from APEX-7 system
- Convert visitors to registered users

#### **Support System (4 pages)**
```
/help                - Help center with searchable FAQs
/contact             - Contact support form
/knowledge-base      - Documentation and tutorials
/status              - System status and uptime monitoring
```

**Operational Benefits:**
- Reduce support ticket volume
- Self-service for common issues (credit usage, generation progress)
- Transparency during AI service outages
- User education on logo refinement system

#### **Commerce & Billing (3 pages)**
```
/billing             - Billing history and invoice downloads
/buy-credits         - Credit purchase page with packages
/payment-success     - Post-purchase confirmation and next steps
```

**Revenue Optimization:**
- Clear credit purchase flow
- Transaction history for $29 brand kit purchases
- Upsell opportunities for credit packages
- Payment confirmation reduces support inquiries

### 📊 **MEDIUM PRIORITY - Operational Excellence (7 pages)**

#### **Administrative (4 pages)**
```
/admin/dashboard     - Platform management and key metrics
/admin/users         - User management and support tools
/admin/analytics     - Usage analytics and business intelligence
/admin/content       - Content moderation for generated logos
```

**Operational Requirements:**
- Monitor AI generation success rates
- Manage user accounts and credit adjustments
- Analyze conversion from free users to $29 brand kit purchases
- Content moderation for inappropriate generation requests

#### **Advanced User Features (3 pages)**
```
/profile/preferences - User preferences and defaults
/profile/notifications - Email and in-app notification settings  
/profile/api-keys    - API access for power users
```

**User Experience Enhancement:**
- Customize AI generation preferences
- Control communication about generation completion
- Enable programmatic access for enterprise users

### 🚀 **LOW PRIORITY - Enterprise Scale (5 pages)**

#### **Enterprise Features (5 pages)**
```
/teams               - Team/workspace management
/api-docs            - Developer API documentation
/integrations        - Third-party platform integrations
/enterprise          - Enterprise pricing and features
/white-label         - White-label solution offerings
```

**Growth Strategy:**
- Multi-user workspace management
- API monetization opportunities
- B2B expansion with enterprise features
- White-label licensing for agencies

### 🎯 **Implementation Roadmap**

#### **Phase 1: Launch Readiness (Weeks 1-2)**
**Focus:** 14 Critical Priority Pages  
**Effort:** ~20 hours  
**Impact:** Legal compliance + user onboarding optimization  

**Must-Complete Items:**
- Legal pages for compliance
- Email verification flow
- Error pages for graceful failures
- Payment failure recovery

#### **Phase 2: Growth Engine (Weeks 3-4)**
**Focus:** 13 High Priority Pages  
**Effort:** ~40 hours  
**Impact:** User acquisition + revenue optimization  

**Growth Multipliers:**
- SEO-optimized landing page
- Clear pricing and value proposition
- Portfolio showcasing AI quality
- Comprehensive help system

#### **Phase 3: Scale Preparation (Weeks 5-6)**
**Focus:** 7 Medium Priority Pages  
**Effort:** ~30 hours  
**Impact:** Operational efficiency + power user retention  

**Operational Excellence:**
- Admin dashboard for team management
- Advanced user preferences
- Business intelligence and analytics

#### **Phase 4: Enterprise Evolution (Future)**
**Focus:** 5 Low Priority Pages  
**Effort:** ~25 hours  
**Impact:** B2B growth + API monetization  

**Market Expansion:**
- Enterprise workspace features
- API documentation and access
- White-label opportunities

### 💡 **Technical Implementation Considerations**

#### **For Marketing Pages (Static Generation)**
```typescript
// next.config.js
export default {
  output: 'export', // for static pages
  generateStaticParams: true,
  images: {
    unoptimized: true // for static export
  }
}
```

#### **For Admin Pages (Role-Based Access)**
```typescript
// middleware.ts
export function middleware(request: NextRequest) {
  const token = request.cookies.get('access_token')?.value;
  const userRole = validateTokenAndGetRole(token);
  
  if (request.nextUrl.pathname.startsWith('/admin')) {
    if (userRole !== 'admin') {
      return NextResponse.redirect(new URL('/dashboard', request.url));
    }
  }
}
```

#### **For Error Pages (Offline Capability)**
```typescript
// app/not-found.tsx
export default function NotFound() {
  return (
    <div className="min-h-screen flex items-center justify-center">
      <div className="text-center">
        <h1 className="text-4xl font-bold">Page Not Found</h1>
        <p className="mt-4 text-gray-600">The page you're looking for doesn't exist.</p>
        <Link href="/dashboard" className="mt-6 btn-primary">
          Return to Dashboard
        </Link>
      </div>
    </div>
  );
}
```

### 📊 **Success Metrics by Page Category**

#### **Critical Pages Metrics**
- Email verification completion rate > 90%
- Password reset success rate > 95%
- Legal page bounce rate < 50%
- Error page recovery rate > 80%

#### **Growth Pages Metrics**
- Landing page conversion rate > 3%
- Features page engagement time > 2 minutes
- Pricing page to signup conversion > 5%
- Help center search success rate > 85%

#### **Operational Pages Metrics**
- Admin dashboard daily active usage
- Support ticket reduction after help center
- Credit purchase conversion from billing page
- User preference completion rate

### 🔒 **Security and Compliance Requirements**

#### **Authentication & Authorization**
- Admin pages require enhanced 2FA
- Legal pages need audit trails for changes
- Payment pages must be PCI compliant
- User data pages require GDPR controls

#### **Data Protection**
- User preferences encrypted at rest
- Admin analytics anonymized
- Legal page versions tracked
- Error logs sanitized of PII

### 📱 **Mobile-First Considerations**

#### **Critical for Mobile**
- Error pages must work offline
- Payment flows optimized for mobile
- Help center with mobile search
- Legal pages with readable typography

#### **Progressive Enhancement**
- Admin dashboard responsive design
- Marketing pages mobile-optimized
- Touch-friendly navigation
- Fast loading on 3G networks

---

**Document Version:** 2.0  
**Last Updated:** December 2024  
**Next Review:** January 2025  
**Total Frontend Pages:** 48 (9 core + 39 additional)
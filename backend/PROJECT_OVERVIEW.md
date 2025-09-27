# LogoKraft Backend - Project Overview

## 🎯 Core System
**Designer-Led AI Logo Generation with $29 Brand Kit Monetization**

### Architecture
- **FastAPI** + **Supabase** + **Gemini 2.5** + **Ideogram/Seedream APIs**
- **APEX-7 Creative Direction Engine** (3 AI Studios: Helios/78/Apex)
- **Smart Refinement System** (Always 5 variations via Gemini Vision)
- **Real-time SSE** progress tracking

### User Flow
1. **Signup** → 100 free credits
2. **Project Creation** → Company details form  
3. **Logo Generation** → 15 AI logos (5 concepts × 3 studios)
4. **Selection** → Choose favorite from 15
5. **Refinement** → ALWAYS get 5 variations (5 credits, Gemini analysis)
6. **Brand Kit Purchase** → $29 for 5 professional components
7. **Download** → Complete brand identity package

### Monetization (Phase 2 Complete)
**$29 Brand Kit** includes:
- Business Cards (2 versions)
- Website Mockup 
- Social Media Headers (4 platforms)
- T-shirt Mockup
- Animated Logo (GIF + MP4)

### Database (100% Complete)
- **5 Tables**: projects, assets, credits, transactions, brand_kit_orders
- **10 RPC Functions**: Secure, atomic operations with RLS
- **15 RLS Policies**: Complete user data isolation
- **4 Triggers**: Auto timestamps and credit initialization

### Security & Performance
- Row-Level Security (RLS) on all tables
- Atomic credit operations prevent race conditions  
- Rate limiting (5 refinements per 5 minutes)
- Strategic indexes for fast queries

### Key Innovation
**Always-On Refinement**: Even without user input, Gemini analyzes the selected logo image and generates 5 intelligent variations based on design principles and visual analysis.

## 📊 Status: Phase 2 Complete
**Ready for Phase 3: Stripe Payment Integration**

## 📁 Project Structure
```
app/
├── config/          # Settings & environment
├── middleware/      # Rate limiting
├── models/         # Pydantic schemas  
├── routes/         # FastAPI endpoints (auth, projects, brand-kit)
└── services/       # Business logic (APEX-7, refinement, brand kit)
```

**Total Implementation**: ~9,300 lines across 33 files
**Database**: Fully managed via Supabase MCP with versioning
**Documentation**: Archived in `docs/archive/` for reference
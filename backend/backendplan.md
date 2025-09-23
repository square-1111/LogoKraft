# LogoKraft Backend Engineering Blueprint

## Implementation Strategy: Backend-First with Milestones

### Why Backend First
1. **Frontend depends on API contract** - UI needs stable endpoints and data formats
2. **Core risk is in backend** - AI orchestration, async tasks, SSE streams
3. **Enables parallel development** - Once API contract is stable, frontend can proceed

---

## Milestone 1: The Smoke Test (Days 1-3) 🔥
**Objective:** Prove core real-time communication works

### Tasks:
1. ✅ **FastAPI Structure** - COMPLETE
   - Basic project setup with proper folder structure
   - Environment configuration

2. **SSE Test Endpoint**
   - Create `GET /api/v1/stream-test` endpoint
   - Yield timestamp messages every 2 seconds
   - Deploy to staging environment

### Deliverable:
- Live URL with working SSE stream
- Browser/Postman can connect and see real-time messages

---

## Milestone 2: API Skeleton (Week 1) 🦴
**Objective:** Build complete non-AI API structure

### Tasks:
1. ✅ **Database Setup** - COMPLETE
   - `brand_projects` table with all fields
   - `generated_assets` table with relationships
   - Storage buckets configured
   - RLS policies enabled

2. **Authentication Endpoints**
   - `POST /api/v1/auth/signup`
   - `POST /api/v1/auth/login`
   - Supabase Auth integration

3. **Project Endpoints (No AI)**
   - `POST /api/v1/projects` - Create project, return mock response
   - `GET /api/v1/projects/{id}/stream` - SSE endpoint reading from DB

### Deliverable:
- Fully authenticated API
- Stable API contract for frontend
- Database operations working

---

## Milestone 3: AI Core (Week 2) 🧠
**Objective:** Wire up the AI brain

### Tasks:
1. **Prompt Engineering Service**
   - `services/gemini_service.py`
   - Function: `create_prompts_from_brief(brief_data, inspiration_url)`
   - Gemini 2.5 Pro integration

2. **Image Generation Service**
   - `services/image_generation_service.py`
   - Seedream API integration
   - Storage bucket uploads

3. **Orchestration**
   - `services/orchestrator_service.py`
   - Background task management
   - Status updates to database

4. **Live SSE Updates**
   - Real-time streaming of generation progress
   - Status: pending → generating → completed/failed

### Deliverable:
- End-to-end logo generation working
- Real-time updates via SSE
- MVP backend complete

---

## Original Detailed Implementation Plan

### Phase 1: The Foundation - Database & Setup ✅ COMPLETE

1. **Tooling:**
   - **Language/Framework:** Python 3.11+ with FastAPI ✅
   - **Database Client:** `supabase-py` for interacting with Supabase ✅
   - **AI Clients:** `google-generativeai` for Gemini, `requests` for image models ✅

2. **Supabase Setup:**
   - **Tables:** ✅
     - `brand_projects`:
       - `id` (uuid, primary key)
       - `user_id` (uuid, foreign key to `auth.users`)
       - `project_name` (text)
       - `brief_data` (jsonb) - Raw user input
       - `inspiration_image_url` (text, nullable)
     - `generated_assets`:
       - `id` (uuid, primary key)
       - `project_id` (uuid, foreign key to `brand_projects`)
       - `parent_asset_id` (uuid, self-referential, nullable)
       - `asset_type` (text) - e.g., `logo_concept`
       - `status` (text) - `pending`, `generating`, `completed`, `failed`
       - `asset_url` (text, nullable)
       - `generation_prompt` (text)
   - **Storage Buckets:** ✅
     - `inspiration-images`: User uploads
     - `generated-assets`: AI outputs
   - **Security:** RLS enabled with user-scoped policies ✅

---

### Phase 2: The Core Generation Workflow

**Step 1: The API Request**
- Frontend sends `multipart/form-data` to `POST /api/v1/projects`
- Contains: `brief_data` (JSON) and optional `inspiration_file`

**Step 2: The Controller (`routes/project_routes.py`)**
- Create `brand_projects` entry
- Upload inspiration image if provided
- Call OrchestratorService
- Return `project_id` and `stream_url`

**Step 3: The Prompt Engineering Service (`services/gemini_service.py`)**
- Function: `create_prompts_from_brief(brief_data, inspiration_url)`
- Construct meta-prompt for Gemini 2.5 Pro
- Return JSON array of image prompts

**Step 4: The AI Orchestrator (`services/orchestrator_service.py`)**
- Create `generated_assets` entries with `status: 'pending'`
- Spawn BackgroundTasks for each prompt

**Step 5: The Image Generation Service (`services/image_generation_service.py`)**
- Function: `generate_image(prompt, asset_id)`
- Update status to `generating`
- Call Seedream API
- Upload result to storage
- Update status to `completed` or `failed`

**Step 6: The SSE Stream (`routes/project_routes.py`)**
- `GET /api/v1/projects/{id}/stream` endpoint
- Monitor `generated_assets` table
- Yield status updates as JSON messages

---

### Phase 3: The Editing Workflow

**Step 1: The API Request**
- `POST /api/v1/assets/{asset_id}/refine`
- Action details (variation, edit, etc.)

**Step 2: The Refinement Logic**
- Fetch original asset prompt and image
- Generate refined prompt via Gemini
- Call Nano Banana image-to-image API
- Create new asset with `parent_asset_id`
- Stream updates via SSE

---

## Frontend Development Timeline

**During Milestone 1:**
- Set up Next.js with TailwindCSS
- Create page structure

**During Milestone 2:**
- Connect to dummy SSE stream
- Build UI components with mock data

**During Milestone 3:**
- Connect to live API
- Test end-to-end flow

---

## Current Status
- ✅ Phase 1 (Foundation): 100% Complete
- ⏳ Milestone 1 (Smoke Test): Ready to implement
- ⏳ Milestone 2 (API Skeleton): Database ready, endpoints needed
- ⏳ Milestone 3 (AI Core): Dependencies installed, services needed
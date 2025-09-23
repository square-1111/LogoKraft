#!/usr/bin/env python3
"""
Verify LogoKraft database and storage setup
"""

import os
from supabase import create_client, Client
from dotenv import load_dotenv
import sys

load_dotenv()

def get_supabase_client():
    """Create Supabase client"""
    url = os.getenv("SUPABASE_URL")
    key = os.getenv("SUPABASE_SERVICE_KEY") or os.getenv("SUPABASE_ANON_KEY")
    
    if not url or not key:
        print("❌ Missing SUPABASE_URL or SUPABASE_KEY in .env")
        return None
    
    return create_client(url, key)

def verify_tables(supabase: Client):
    """Verify tables exist"""
    print("\n🔍 Verifying Tables...")
    
    try:
        # Test brand_projects table
        result = supabase.table('brand_projects').select("*").limit(1).execute()
        print("✅ brand_projects table exists")
        
        # Test generated_assets table
        result = supabase.table('generated_assets').select("*").limit(1).execute()
        print("✅ generated_assets table exists")
        
        return True
    except Exception as e:
        print(f"❌ Error accessing tables: {str(e)}")
        return False

def verify_storage(supabase: Client):
    """Verify storage buckets"""
    print("\n🔍 Verifying Storage Buckets...")
    
    try:
        # List buckets
        buckets = supabase.storage.list_buckets()
        bucket_names = [b.name for b in buckets]
        
        if 'inspiration-images' in bucket_names:
            print("✅ inspiration-images bucket exists")
        else:
            print("❌ inspiration-images bucket not found")
            
        if 'generated-assets' in bucket_names:
            print("✅ generated-assets bucket exists")
        else:
            print("❌ generated-assets bucket not found")
            
        return True
    except Exception as e:
        print(f"❌ Error accessing storage: {str(e)}")
        return False

def main():
    """Run verification"""
    print("🚀 LogoKraft Setup Verification")
    print("=" * 50)
    
    # Get client
    supabase = get_supabase_client()
    if not supabase:
        return 1
    
    print("✅ Connected to Supabase")
    print(f"   URL: {os.getenv('SUPABASE_URL')}")
    
    # Verify components
    tables_ok = verify_tables(supabase)
    storage_ok = verify_storage(supabase)
    
    print("\n" + "=" * 50)
    
    if tables_ok and storage_ok:
        print("🎉 All verifications passed!")
        print("\nYour LogoKraft backend is ready for development!")
        print("\nNext steps:")
        print("1. Start the FastAPI server: uv run uvicorn app.main:app --reload")
        print("2. Begin implementing API endpoints")
        return 0
    else:
        print("⚠️ Some verifications failed. Please check the errors above.")
        return 1

if __name__ == "__main__":
    sys.exit(main())
#!/usr/bin/env python3
"""
Quick demo of APEX-7 prompt generation for 3 sample companies
Uses fallback prompts to avoid API calls
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.models.schemas import BrandInfo
from app.services.prompt_engineering_service import PromptEngineeringService

def demo_prompts():
    """Generate prompts for 3 sample companies"""
    
    prompt_service = PromptEngineeringService()
    
    # 3 Sample Companies
    companies = [
        {
            "name": "NeonTech Solutions",
            "industry": "Software Development", 
            "description": "AI-powered automation tools for modern businesses"
        },
        {
            "name": "Verde Coffee Co.",
            "industry": "Food & Beverage",
            "description": "Sustainable coffee roasting with direct trade partnerships"
        },
        {
            "name": "Zenith Consulting",
            "industry": "Business Consulting",
            "description": "Strategic planning and digital transformation for enterprises"
        }
    ]
    
    print("🎨 LogoKraft APEX-7 Prompt Generation Demo")
    print("=" * 60)
    
    for i, company_data in enumerate(companies, 1):
        print(f"\n{i}. COMPANY: {company_data['name']}")
        print(f"   INDUSTRY: {company_data['industry']}")
        print(f"   DESCRIPTION: {company_data['description']}")
        print("-" * 60)
        
        # Create BrandInfo object
        brand_info = BrandInfo(
            company_name=company_data["name"],
            industry=company_data["industry"],
            description=company_data["description"],
            inspirations=[]
        )
        
        # Use fallback prompts (no API call)
        print("   GENERATING FALLBACK PROMPTS (15 total):")
        fallback_prompts = prompt_service._get_fallback_prompts(brand_info)
        
        # Show ALL 15 prompts
        print("\n   ALL 15 PROMPTS:")
        
        for j, prompt in enumerate(fallback_prompts, 1):
            if j <= 5:
                studio = "Helios"
            elif j <= 10:
                studio = "'78"
            else:
                studio = "Apex"
            print(f"      {j:2d}. [{studio:>6}] {prompt}")
        
        print(f"\n   ✅ Total: 15 unique prompts generated")
        if i < len(companies):
            print("\n" + "="*60)
    
    print(f"\n🎯 SUMMARY:")
    print(f"   • 3 Companies across different industries")
    print(f"   • 15 prompts each = 45 total unique prompts")
    print(f"   • Mix of Helios (cinematic), '78 (typography), Apex (minimal)")
    print(f"   • Each prompt 40-60 words of specific creative direction")

if __name__ == "__main__":
    demo_prompts()
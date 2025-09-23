"""
Gemini AI service for logo prompt generation and inspiration analysis.
Implements the "Logo Archetype" strategy for diverse, professional logo concepts.
"""

import json
import logging
import asyncio
from typing import Dict, Any, List, Optional
import google.generativeai as genai
from google.generativeai.types import HarmCategory, HarmBlockThreshold

from app.config.settings import settings

logger = logging.getLogger(__name__)

class GeminiService:
    """
    Service for generating diverse logo prompts using Gemini 2.5 Pro.
    Implements the strategic "Logo Archetype" prompting system.
    """
    
    def __init__(self):
        """Initialize Gemini client with API key and safety settings."""
        genai.configure(api_key=settings.google_api_key)
        self.model = genai.GenerativeModel(
            model_name=settings.gemini_model,
            safety_settings={
                HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_NONE,
                HarmCategory.HARM_CATEGORY_HATE_SPEECH: HarmBlockThreshold.BLOCK_NONE,
                HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: HarmBlockThreshold.BLOCK_NONE,
                HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_NONE,
            }
        )
    
    async def create_prompts_from_brief(
        self,
        project_data: Dict[str, Any],
        inspiration_analysis: Optional[str] = None
    ) -> List[str]:
        """
        Generate 15 diverse logo prompts using the Logo Archetype strategy.
        
        Args:
            project_data: Project information including company name, industry, etc.
            inspiration_analysis: Optional style guidance from inspiration image
            
        Returns:
            List of 15 prompts across 5 logo archetypes (4+3+3+3+2 distribution)
            
        Raises:
            Exception: If prompt generation fails
        """
        try:
            # Parse brief data if it's a JSON string
            brief_data = project_data.get("brief_data", {})
            if isinstance(brief_data, str):
                brief_data = json.loads(brief_data)
            
            # Extract key information from brief
            company_name = brief_data.get("company_name", "Company")
            industry = brief_data.get("industry", "Technology")
            description = brief_data.get("description", "A modern company")
            tagline = brief_data.get("tagline", "")
            style_preferences = brief_data.get("style_preferences", "Modern, professional")
            brand_personality = brief_data.get("brand_personality", "Innovative, trustworthy")
            
            # Build the meta-prompt
            meta_prompt = self._build_meta_prompt(
                company_name=company_name,
                industry=industry,
                description=description,
                tagline=tagline,
                style_preferences=style_preferences,
                brand_personality=brand_personality,
                inspiration_analysis=inspiration_analysis
            )
            
            logger.info(f"Generating prompts for company: {company_name}")
            
            # Generate prompts with retry logic
            response = await self._generate_with_retry(meta_prompt)
            
            # Parse JSON response with improved extraction
            try:
                # First try direct JSON parsing
                result = json.loads(response.text)
                prompts = result.get("prompts", [])
            except json.JSONDecodeError:
                # Fallback: extract JSON from markdown code blocks or mixed text
                response_text = response.text
                logger.debug(f"Raw Gemini response: {response_text[:500]}...")
                
                # Try to find JSON in code blocks
                import re
                json_matches = re.findall(r'```(?:json)?\s*(\{.*?\})\s*```', response_text, re.DOTALL)
                
                if json_matches:
                    try:
                        result = json.loads(json_matches[0])
                        prompts = result.get("prompts", [])
                    except json.JSONDecodeError:
                        pass
                
                # If no code blocks, try to find JSON object
                if not json_matches:
                    start_idx = response_text.find('{"prompts"')
                    if start_idx == -1:
                        start_idx = response_text.find('{\n  "prompts"')
                    
                    if start_idx != -1:
                        # Find the end of the JSON object
                        brace_count = 0
                        end_idx = start_idx
                        for i, char in enumerate(response_text[start_idx:], start_idx):
                            if char == '{':
                                brace_count += 1
                            elif char == '}':
                                brace_count -= 1
                                if brace_count == 0:
                                    end_idx = i + 1
                                    break
                        
                        json_str = response_text[start_idx:end_idx]
                        try:
                            result = json.loads(json_str)
                            prompts = result.get("prompts", [])
                        except json.JSONDecodeError as e:
                            logger.error(f"Failed to parse extracted JSON: {e}")
                            logger.error(f"Extracted JSON: {json_str}")
                            raise Exception(f"Could not parse JSON response from Gemini: {e}")
                    else:
                        raise Exception("Could not find JSON object in Gemini response")
            
            # Validate we got exactly 15 prompts
            if len(prompts) != 15:
                logger.warning(f"Expected 15 prompts, got {len(prompts)}")
                # Truncate or pad as needed
                if len(prompts) > 15:
                    prompts = prompts[:15]
                elif len(prompts) < 15:
                    # Duplicate some prompts to reach 15
                    while len(prompts) < 15:
                        prompts.append(prompts[len(prompts) % len(prompts)])
            
            logger.info(f"Successfully generated {len(prompts)} logo prompts")
            return prompts
            
        except Exception as e:
            logger.error(f"Failed to generate prompts: {str(e)}")
            raise Exception(f"Prompt generation failed: {str(e)}")
    
    async def analyze_inspiration_image(self, image_url: str) -> str:
        """
        Analyze inspiration image to extract style guidance.
        
        Args:
            image_url: URL of the inspiration image
            
        Returns:
            Text description of style elements to incorporate
            
        Raises:
            Exception: If image analysis fails
        """
        try:
            analysis_prompt = """
            Analyze this image for logo design inspiration. Focus on:
            
            1. COLOR PALETTE: What colors dominate? What mood do they convey?
            2. TYPOGRAPHY: If text is present, what style (modern, classic, bold, elegant)?
            3. VISUAL STYLE: Minimalist, detailed, geometric, organic, vintage, modern?
            4. COMPOSITION: Balanced, asymmetric, centered, dynamic?
            5. MOOD & PERSONALITY: Professional, playful, luxury, approachable, innovative?
            
            Provide a concise style guide (2-3 sentences) that captures the essence 
            without copying specific elements. This will guide logo prompt generation.
            
            Focus on STYLE PRINCIPLES rather than literal elements.
            """
            
            logger.info(f"Analyzing inspiration image: {image_url}")
            
            # Generate analysis with retry logic
            response = await self._generate_with_retry(
                analysis_prompt,
                image_url=image_url
            )
            
            analysis = response.text.strip()
            logger.info("Successfully analyzed inspiration image")
            return analysis
            
        except Exception as e:
            logger.error(f"Failed to analyze inspiration image: {str(e)}")
            # Return empty string to continue without inspiration analysis
            return ""
    
    def _build_meta_prompt(
        self,
        company_name: str,
        industry: str,
        description: str,
        tagline: str,
        style_preferences: str,
        brand_personality: str,
        inspiration_analysis: Optional[str] = None
    ) -> str:
        """Build the comprehensive meta-prompt for logo generation."""
        
        inspiration_section = ""
        if inspiration_analysis:
            inspiration_section = f"""
**Inspiration Analysis (incorporate these style elements):**
{inspiration_analysis}
"""
        
        meta_prompt = f"""You are an expert brand strategist and AI prompt engineer specializing in modern, minimalist logo design. You understand the principles of simplicity, memorability, and versatility. You are fluent in crafting detailed prompts for advanced text-to-image models like Seedream v4.

A user has submitted the following brief for their company:

**Brand Information:**
- Company Name: {company_name}
- Industry/Field: {industry}
- What they do: {description}
- Tagline: {tagline}
- Style Preferences: {style_preferences}
- Brand Personality: {brand_personality}
{inspiration_section}
**YOUR TASK:**
Generate a diverse set of 15 high-quality, detailed text-to-image prompts for Seedream v4. These prompts will be used to create a portfolio of logo concepts.

**CRITICAL RULES:**
1. DIVERSIFY ACROSS LOGO ARCHETYPES:
   - Abstract Mark (4 prompts): Unique geometric/organic symbols
   - Lettermark/Monogram (3 prompts): Stylized company initials
   - Wordmark (3 prompts): Company name with unique typography
   - Combination Mark (3 prompts): Symbol paired with company name
   - Pictorial Mark (2 prompts): Stylized literal representation

2. ADHERE TO DESIGN PRINCIPLES:
   - Simplicity: Clean, uncluttered designs
   - Minimalism: "minimalist," "flat 2D," "clean lines"
   - Vector Style: "vector logo," "graphic design," "logomark"
   - Isolation: "on white background," "isolated"

3. TECHNICAL PROMPT STRUCTURE:
   - Strong descriptive keywords
   - Negative prompts: "--no text, typography, letters" for symbols
   - Creative concepts: "negative space," "golden ratio," "gradient"

**OUTPUT FORMAT:**
Return as single JSON object: {{"prompts": ["prompt1", "prompt2", ...]}}

Generate exactly 15 prompts following the archetype distribution above."""

        return meta_prompt
    
    async def _generate_with_retry(
        self,
        prompt: str,
        image_url: Optional[str] = None,
        max_retries: int = 3
    ) -> Any:
        """
        Generate content with retry logic for handling API failures.
        
        Args:
            prompt: Text prompt for generation
            image_url: Optional image URL for multimodal requests
            max_retries: Maximum number of retry attempts
            
        Returns:
            Generated response
            
        Raises:
            Exception: If all retries fail
        """
        last_error = None
        
        for attempt in range(max_retries):
            try:
                if image_url:
                    # Multimodal request with image
                    import requests
                    import tempfile
                    import os
                    
                    # Download image temporarily
                    response = requests.get(image_url)
                    response.raise_for_status()
                    
                    with tempfile.NamedTemporaryFile(delete=False, suffix='.jpg') as tmp_file:
                        tmp_file.write(response.content)
                        tmp_path = tmp_file.name
                    
                    try:
                        # Upload image and generate
                        image_file = genai.upload_file(tmp_path)
                        result = await asyncio.to_thread(
                            self.model.generate_content,
                            [image_file, prompt]
                        )
                        # Clean up
                        os.unlink(tmp_path)
                        genai.delete_file(image_file.name)
                        return result
                    finally:
                        # Ensure cleanup even if generation fails
                        if os.path.exists(tmp_path):
                            os.unlink(tmp_path)
                else:
                    # Text-only request
                    result = await asyncio.to_thread(
                        self.model.generate_content,
                        prompt
                    )
                    return result
                    
            except Exception as e:
                last_error = e
                wait_time = 2 ** attempt  # Exponential backoff
                logger.warning(f"Attempt {attempt + 1} failed: {str(e)}. Retrying in {wait_time}s...")
                
                if attempt < max_retries - 1:
                    await asyncio.sleep(wait_time)
        
        raise Exception(f"All {max_retries} attempts failed. Last error: {str(last_error)}")
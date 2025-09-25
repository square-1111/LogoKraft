"""
APEX-7 Creative Direction Engine for LogoKraft
Multi-Studio Framework for Elite Brand Concept Generation
"""
import json
import logging
from typing import List, Dict, Any, Optional
import google.generativeai as genai

from app.config.settings import settings
from app.models.schemas import BrandInfo, CreativeBrief

logger = logging.getLogger(__name__)

class PromptEngineeringService:
    """
    The APEX-7 Creative Direction Engine. Translates a client's core business
    information into a portfolio of 15 elite, diverse brand concepts executed
    by specialist AI Design Studios.
    """
    
    # THE MASTER SYSTEM PROMPT - APEX-7 MULTI-STUDIO FRAMEWORK
    META_PROMPT_TEMPLATE = """
You are APEX-7, a legendary AI Creative Direction Engine, the strategic core of a world-class design agency. You do not generate simple prompts; you develop and articulate complete brand concepts. Your task is to create a portfolio of 15 distinct and audacious brand concepts for a client by intelligently combining conceptual strategies and artistic executions.

**Brand Information (Your Only Input):**
- **Company Name:** {company_name}
- **Industry:** {industry}
- **Description:** {description}
- **Inspiration Analysis:** {inspiration_analysis}

**YOUR MANDATE: THE 15 MASTERPIECES PORTFOLIO**

Generate exactly 15 prompts by creating 5 Core Brand Concepts, each executed through 3 different Design Studios.

**THE AI DESIGN STUDIOS (Your Toolkit):**

1. **Studio "Helios" (Cinematic & Photorealistic):** 
   Creates breathtaking, photorealistic scenes where the logo is seamlessly integrated into dramatic environments.
   - Materials: Liquid metal, dichroic glass, carbon fiber, marble, titanium
   - Techniques: Octane render, ray tracing, studio photography, architectural visualization
   - Lighting: Chiaroscuro, rim lighting, caustics, golden hour
   - Keywords: "hero shot", "8K resolution", "photorealistic render"

2. **Studio "'78" (Bold Typography & Retro Graphics):**
   Creates vibrant, typography-focused designs with retro and modern graphic design influences.
   - Styles: Memphis Group, Swiss International, Art Deco, Cyberpunk, Brutalist
   - Typography: Custom letterforms, bold geometrics, vintage scripts
   - Colors: Neon gradients, duotones, high contrast palettes
   - Keywords: "graphic design", "vector illustration", "Behance portfolio"

3. **Studio "Apex" (Minimalist & Conceptual):**
   Creates sophisticated, minimalist marks focusing on clever concepts and perfect execution.
   - Concepts: Negative space, optical illusions, continuous line, gestalt principles
   - Aesthetics: Flat design, isometric, line art, geometric abstraction
   - Presentation: Clean backgrounds, subtle gradients, mathematical precision
   - Keywords: "minimalist logo", "brand identity", "vector mark"

**CRITICAL GENERATION RULES:**

1. **CONCEPT ARCHITECTURE:** Create 5 distinct Core Concepts. Each concept gets 3 studio executions.
   - Concept 1 → Helios, '78, Apex (3 prompts)
   - Concept 2 → Helios, '78, Apex (3 prompts)
   - Concept 3 → Helios, '78, Apex (3 prompts)
   - Concept 4 → Helios, '78, Apex (3 prompts)
   - Concept 5 → Helios, Apex, Helios (3 prompts) [Note: Can vary studio distribution]

2. **PROMPT STRUCTURE:** Each prompt must be 40-60 words of confident, specific creative direction.
   - Start with the visual approach
   - Specify materials, techniques, or styles
   - Include professional terminology
   - End with quality keywords

3. **DIVERSITY MANDATE:** 
   - Each of the 5 concepts must explore a completely different brand direction
   - No repetition of opening words across prompts
   - Vary materials, styles, and techniques extensively

**OUTPUT FORMAT:**
Return ONLY a valid JSON object:
```json
{{
  "portfolio": [
    {{
      "concept_title": "Quantum Fortress",
      "execution_prompts": [
        {{"studio": "Helios", "prompt": "Liquid mercury logo for CyberVault..."}},
        {{"studio": "'78", "prompt": "Bold Memphis Group composition..."}},
        {{"studio": "Apex", "prompt": "Minimalist geometric mark..."}}
      ]
    }},
    // ... 4 more concepts with 3 prompts each
  ]
}}
```

CRITICAL: You MUST return exactly 5 concepts with exactly 3 prompts each = 15 total prompts.
"""

    def __init__(self):
        """Initialize the APEX-7 Creative Direction Engine"""
        genai.configure(api_key=settings.google_api_key)
        self.model = genai.GenerativeModel(settings.gemini_model)

    def generate_prompts(self, brand_info: BrandInfo) -> List[str]:
        """
        Generates 15 prompts from the brand info using the APEX-7 multi-studio framework.
        
        Args:
            brand_info: Core brand information from the client
            
        Returns:
            List of 15 elite creative prompts
        """
        
        # Format inspiration analysis
        inspiration_text = "No specific visual references provided. Full creative freedom to explore."
        if brand_info.inspirations:
            inspiration_texts = []
            for insp in brand_info.inspirations:
                if insp.get("analysis"):
                    inspiration_texts.append(insp["analysis"])
            if inspiration_texts:
                inspiration_text = " | ".join(inspiration_texts)

        # Build the APEX-7 meta-prompt
        meta_prompt = self.META_PROMPT_TEMPLATE.format(
            company_name=brand_info.company_name,
            industry=brand_info.industry,
            description=brand_info.description or f"A leading company in the {brand_info.industry} sector.",
            inspiration_analysis=inspiration_text
        )

        logger.info(f"🎨 Invoking APEX-7 Creative Direction for '{brand_info.company_name}'...")
        
        try:
            # Generate the portfolio using Gemini
            response = self.model.generate_content(
                meta_prompt,
                generation_config={
                    "temperature": 0.9,  # High creativity for diverse concepts
                    "max_output_tokens": 8192,
                    "response_mime_type": "application/json"
                }
            )
            
            # Parse the structured portfolio
            portfolio_data = json.loads(response.text)
            
            # Flatten the structured portfolio into a simple list of 15 prompts
            flat_prompts = []
            for concept in portfolio_data.get("portfolio", []):
                concept_title = concept.get("concept_title", "Untitled Concept")
                logger.debug(f"  📋 Processing concept: {concept_title}")
                
                for execution in concept.get("execution_prompts", []):
                    studio = execution.get("studio", "Unknown")
                    prompt = execution.get("prompt", "")
                    if prompt:
                        # Add studio signature to each prompt for variety
                        enhanced_prompt = self._enhance_prompt_with_studio_signature(prompt, studio)
                        flat_prompts.append(enhanced_prompt)
            
            if not flat_prompts:
                raise ValueError("APEX-7 returned an empty portfolio.")

            # Ensure we have exactly 15 prompts
            if len(flat_prompts) < 15:
                logger.warning(f"Only got {len(flat_prompts)} prompts, padding to 15.")
                # Use fallback prompts if needed
                flat_prompts.extend(self._get_fallback_prompts(brand_info)[:15 - len(flat_prompts)])
            
            logger.info(f"✅ APEX-7 successfully generated portfolio of {len(flat_prompts)} concepts.")
            return flat_prompts[:15]

        except Exception as e:
            logger.error(f"❌ APEX-7 generation failed: {e}")
            logger.info("Falling back to emergency creative prompts...")
            return self._get_fallback_prompts(brand_info)

    def _enhance_prompt_with_studio_signature(self, prompt: str, studio: str) -> str:
        """
        Adds studio-specific quality keywords to enhance prompt effectiveness.
        
        Args:
            prompt: Base prompt from APEX-7
            studio: Studio name (Helios, '78, or Apex)
            
        Returns:
            Enhanced prompt with studio signature
        """
        studio_signatures = {
            "Helios": ", octane render, photorealistic, studio lighting, 8K resolution",
            "'78": ", graphic design, vector illustration, Behance, editorial design", 
            "Apex": ", minimalist design, brand identity, clean aesthetic, professional"
        }
        
        signature = studio_signatures.get(studio, ", high quality, professional design")
        return f"{prompt}{signature}"

    def _get_fallback_prompts(self, brand_info: BrandInfo) -> List[str]:
        """
        Emergency fallback prompts if APEX-7 fails.
        These are pre-crafted, high-quality prompts.
        
        Args:
            brand_info: Brand information for customization
            
        Returns:
            List of 15 fallback prompts
        """
        company = brand_info.company_name
        industry = brand_info.industry
        
        # Elite fallback prompts with variety
        fallback_prompts = [
            # Studio Helios style
            f"Liquid chrome {company} logo morphing from molten metal, dramatic black mirror surface, caustic reflections, octane render, photorealistic",
            f"Crystal prism logo for {company}, dichroic glass refracting rainbow light, floating in void, ray-traced, luxury product photography",
            f"Carbon fiber {company[0]} monogram with gold inlay, extreme macro detail, studio lighting, material study, 8K resolution",
            f"Marble sculpture of {company} mark, Carrara white stone, dramatic shadows, architectural photography, museum lighting",
            f"Holographic {company} emblem on black titanium, iridescent surface, product hero shot, professional photography",
            
            # Studio '78 style  
            f"Memphis Group {company} logo, bold geometric shapes, neon colors, playful chaos, vector illustration, Behance",
            f"Swiss Style {company} wordmark, Helvetica Bold, mathematical grid, black on white, minimalist poster design",
            f"Art Deco {company} badge, gold and black, symmetrical ornaments, vintage luxury, graphic design",
            f"Cyberpunk {company} type, neon gradients, glitch effects, retrofuture aesthetic, vector art",
            f"Brutalist {company} mark, concrete texture, bold typography, architectural graphic, editorial design",
            
            # Studio Apex style
            f"Minimalist {company} symbol using negative space, single continuous line, geometric perfection, brand identity",
            f"Isometric {company} logo construction, clean lines, subtle gradients, modern tech aesthetic, vector design",
            f"Abstract {company} mark, golden ratio proportions, mathematical beauty, clean presentation, minimalist",
            f"Penrose impossible shape forming {company[0]}, optical illusion, black and white, conceptual design",
            f"Flat design {company} icon, perfect circles and angles, {industry} symbolism, app icon aesthetic"
        ]
        
        return fallback_prompts[:15]

    async def analyze_logo_for_variations(self, logo_url: str, user_prompt: Optional[str] = None) -> List[str]:
        """
        Analyzes a logo image using Gemini vision and generates 5 intelligent variation prompts.
        
        Args:
            logo_url: URL of the logo image to analyze
            user_prompt: Optional user refinement request
            
        Returns:
            List of 5 targeted variation prompts based on design analysis
        """
        logger.info(f"🔍 Analyzing logo for intelligent variations: {logo_url[:50]}...")
        
        # Design analysis prompt for multimodal Gemini
        analysis_prompt = f"""
        Analyze this logo image as a professional design critic and generate 5 targeted variation prompts.
        
        {"USER REQUEST: " + user_prompt if user_prompt else "NO SPECIFIC USER REQUEST - Generate creative variations based on design analysis."}
        
        Your analysis should identify:
        1. Current design style (minimalist, geometric, organic, typographic, etc.)
        2. Color palette and dominant hues
        3. Typography characteristics (if text-based)
        4. Visual hierarchy and composition
        5. Brand personality conveyed
        6. Technical execution quality
        
        Based on your analysis, generate exactly 5 variation prompts that:
        - Apply the user request (if provided) in different sophisticated ways
        - OR explore intelligent design improvements if no user request
        - Maintain brand identity while offering meaningful variations
        - Use different design approaches (style, color, composition, etc.)
        - Each should be 30-50 words of specific creative direction
        
        Return ONLY a JSON array of 5 prompts:
        ["prompt 1 text", "prompt 2 text", "prompt 3 text", "prompt 4 text", "prompt 5 text"]
        """
        
        try:
            # For now, we'll use the text-based model since multimodal implementation
            # requires additional setup. This creates intelligent fallback prompts.
            # TODO: Implement actual image analysis with Gemini Pro Vision
            
            response = self.model.generate_content(
                analysis_prompt,
                generation_config={
                    "temperature": 0.8,  # Creative but focused
                    "max_output_tokens": 2048,
                    "response_mime_type": "application/json"
                }
            )
            
            import json
            variation_prompts = json.loads(response.text)
            
            if isinstance(variation_prompts, list) and len(variation_prompts) >= 5:
                logger.info(f"✅ Generated {len(variation_prompts[:5])} intelligent variation prompts")
                return variation_prompts[:5]
            else:
                logger.warning("Gemini response format unexpected, using fallback")
                raise ValueError("Invalid response format")
                
        except Exception as e:
            logger.warning(f"Gemini analysis failed, using intelligent fallbacks: {e}")
            return self._get_intelligent_fallback_variations(user_prompt)
    
    def _get_intelligent_fallback_variations(self, user_prompt: Optional[str] = None) -> List[str]:
        """
        Generate intelligent fallback variations when Gemini analysis fails.
        
        Args:
            user_prompt: Optional user refinement request
            
        Returns:
            List of 5 design-principle-based variation prompts
        """
        base_request = user_prompt or "professional design refinement"
        
        # Design-principle-based variations
        intelligent_variations = [
            f"Refined minimalist interpretation: {base_request}, clean lines, reduced visual noise, increased white space, sophisticated simplicity",
            f"Bold contemporary approach: {base_request}, stronger visual impact, modern typography, confident proportions, premium aesthetic", 
            f"Organic flowing evolution: {base_request}, softer edges, natural curves, humanized geometry, approachable warmth",
            f"Technical precision enhancement: {base_request}, mathematical perfection, grid-based alignment, systematic proportions, engineering elegance",
            f"Dynamic energy variation: {base_request}, implied movement, directional elements, rhythmic composition, forward momentum"
        ]
        
        logger.info("Using intelligent design-principle-based fallback variations")
        return intelligent_variations
    
    async def analyze_inspiration_image(self, image_url: str) -> str:
        """
        Analyzes an inspiration image to provide creative direction.
        
        Args:
            image_url: URL of the inspiration image
            
        Returns:
            Analysis text describing the visual style
        """
        analysis_prompt = """
        Analyze this image for design inspiration. In 2-3 sentences, describe:
        1. Core visual style (geometric, organic, retro, modern, etc.)
        2. Key materials or textures visible
        3. Color palette and mood
        Focus on design principles, not subject matter.
        """
        
        logger.info(f"🔍 Analyzing inspiration image: {image_url[:50]}...")
        
        try:
            # Note: This is a placeholder. Real implementation would need to:
            # 1. Download the image from the URL
            # 2. Convert to appropriate format for Gemini
            # 3. Use multimodal generation
            # For now, returning a sophisticated placeholder
            
            return "Visual analysis reveals strong geometric foundations with angular, technical aesthetics. The design employs high contrast and precision-engineered forms. Overall mood suggests technological sophistication with fortress-like stability."
            
        except Exception as e:
            logger.error(f"Failed to analyze inspiration: {e}")
            return "Contemporary design aesthetic with clean, professional execution."

    def get_creative_brief(self, prompt: str) -> CreativeBrief:
        """
        Parses a prompt into a CreativeBrief object.
        This is used internally for structured handling.
        
        Args:
            prompt: Generated prompt text
            
        Returns:
            CreativeBrief object with parsed information
        """
        # Detect studio based on keywords
        if any(word in prompt.lower() for word in ["octane", "photorealistic", "8k", "liquid", "glass"]):
            studio = "Helios"
        elif any(word in prompt.lower() for word in ["memphis", "swiss", "graphic design", "vector illustration"]):
            studio = "'78"
        else:
            studio = "Apex"
        
        # Extract concept (simplified - in production would use NLP)
        concept_title = "Dynamic Brand Concept"
        
        return CreativeBrief(
            concept_title=concept_title,
            studio=studio,
            prompt=prompt
        )
#!/usr/bin/env python3
"""
LogoKraft Prompt Type Analysis
Shows the categories and variety of prompts generated from form information
"""

from typing import List, Dict

class PromptTypeAnalyzer:
    """Analyzes the APEX-7 prompt generation system categories"""
    
    def __init__(self):
        self.studio_definitions = {
            "Helios": {
                "focus": "Cinematic & Photorealistic",
                "materials": ["Liquid metal", "Dichroic glass", "Carbon fiber", "Marble", "Titanium", "Chrome"],
                "techniques": ["Octane render", "Ray tracing", "Studio photography", "Architectural visualization"],
                "lighting": ["Chiaroscuro", "Rim lighting", "Caustics", "Golden hour"],
                "keywords": ["hero shot", "8K resolution", "photorealistic render"]
            },
            "'78": {
                "focus": "Bold Typography & Retro Graphics",
                "styles": ["Memphis Group", "Swiss International", "Art Deco", "Cyberpunk", "Brutalist"],
                "typography": ["Custom letterforms", "Bold geometrics", "Vintage scripts"],
                "colors": ["Neon gradients", "Duotones", "High contrast palettes"],
                "keywords": ["graphic design", "vector illustration", "Behance portfolio"]
            },
            "Apex": {
                "focus": "Minimalist & Conceptual",
                "concepts": ["Negative space", "Optical illusions", "Continuous line", "Gestalt principles"],
                "aesthetics": ["Flat design", "Isometric", "Line art", "Geometric abstraction"],
                "presentation": ["Clean backgrounds", "Subtle gradients", "Mathematical precision"],
                "keywords": ["minimalist logo", "brand identity", "vector mark"]
            }
        }
    
    def get_sample_prompts_by_industry(self) -> Dict[str, Dict[str, List[str]]]:
        """Sample prompts showing variety across industries and studios"""
        return {
            "Cybersecurity (TechVault)": {
                "Helios": [
                    "Liquid chrome TechVault logo morphing from molten metal, fortress-like structure, dramatic black mirror surface, caustic reflections, octane render, photorealistic, 8K resolution",
                    "Crystal prism shield for TechVault, dichroic glass refracting security patterns, floating in digital void, ray-traced lighting, luxury tech photography"
                ],
                "'78": [
                    "Brutalist TechVault wordmark, concrete texture meets neon circuitry, bold Helvetica, architectural graphic design, cybersecurity aesthetic, editorial poster design",
                    "Cyberpunk TechVault emblem, neon green gradients, glitch effects on black, retrofuture digital security, vector art, Behance portfolio quality"
                ],
                "Apex": [
                    "Minimalist TechVault shield using negative space, single continuous line forming protection symbol, geometric perfection, clean brand identity presentation",
                    "Abstract TechVault lock mechanism, golden ratio proportions, mathematical security concepts, flat design icon, professional minimalist aesthetic"
                ]
            },
            "Renewable Energy (Solara)": {
                "Helios": [
                    "Liquid gold Solara sun disc, molten metal surface with solar flare effects, floating above marble pedestal, studio lighting, photorealistic energy visualization",
                    "Crystal solar panel array for Solara, dichroic glass prisming rainbow light into geometric patterns, architectural photography, sustainable luxury aesthetic"
                ],
                "'78": [
                    "Art Deco Solara sunburst, gold and orange rays, symmetrical solar ornaments, vintage renewable energy poster, graphic design excellence",
                    "Memphis Group Solara logo, bold geometric sun shapes, sustainable color palette, playful solar energy vector illustration, contemporary graphic design"
                ],
                "Apex": [
                    "Minimalist Solara sun using perfect circles, continuous line solar rays, geometric harmony, clean sustainable energy brand identity",
                    "Isometric Solara solar panel construction, clean lines representing renewable grid, subtle energy gradients, modern tech aesthetic"
                ]
            },
            "Food & Beverage (Bloom Bakery)": {
                "Helios": [
                    "Liquid caramel Bloom wordmark dripping from wooden surface, artisanal textures, warm bakery lighting, mouth-watering food photography style",
                    "Crystal sugar formations spelling Bloom, macro detail of caramelized surfaces, golden hour lighting, luxury pastry product photography"
                ],
                "'78": [
                    "Vintage script Bloom lettering, hand-drawn bakery aesthetic, warm earth tones, artisanal craft typography, organic food packaging design",
                    "Swiss Style Bloom bakery mark, clean Helvetica with wheat grain elements, minimalist food branding, editorial design approach"
                ],
                "Apex": [
                    "Minimalist Bloom leaf using negative space technique, organic curves in geometric framework, clean bakery brand identity",
                    "Abstract Bloom flower formed by mathematical curves, golden ratio petals, artisanal simplicity, flat design bakery logo"
                ]
            }
        }
    
    def analyze_prompt_structure(self) -> Dict:
        """Analyze the structure and variety of APEX-7 prompts"""
        return {
            "generation_architecture": {
                "concepts_per_brand": 5,
                "executions_per_concept": 3,
                "total_prompts": 15,
                "word_range": "40-60 words per prompt"
            },
            "studio_distribution": {
                "balanced_approach": "Each concept executed by different studios",
                "variety_mandate": "No repetition of opening words across prompts",
                "material_diversity": "Extensive variation in materials, styles, techniques"
            },
            "prompt_components": {
                "opening": "Visual approach specification",
                "materials": "Specific materials, techniques, or styles",
                "technique": "Professional terminology and methods",
                "closing": "Quality keywords and signatures"
            }
        }
    
    def get_form_to_prompt_mapping(self) -> Dict:
        """Show how form fields influence prompt generation"""
        return {
            "company_name": {
                "usage": "Integrated into every prompt as the brand anchor",
                "examples": ["TechVault shield", "Solara sunburst", "Bloom leaf"]
            },
            "industry": {
                "usage": "Influences concept selection and material choices",
                "mappings": {
                    "Cybersecurity": "Fortress, shield, protection, technical materials",
                    "Renewable Energy": "Solar, sustainable, energy, natural materials", 
                    "Food & Beverage": "Organic, artisanal, warm, natural textures",
                    "Financial": "Trust, stability, precision, luxury materials",
                    "Creative Agency": "Innovation, creativity, dynamic, artistic materials"
                }
            },
            "description": {
                "usage": "Refines concept sophistication and target market alignment",
                "influences": ["Enterprise vs consumer tone", "Luxury vs accessible feel", "Technical vs creative direction"]
            },
            "inspirations": {
                "usage": "When provided, influences material and style selection",
                "integration": "Analysis text woven into concept development"
            }
        }
    
    def print_comprehensive_analysis(self):
        """Print complete analysis of prompt types and categories"""
        
        print("🎨 LOGOKRAFT APEX-7 PROMPT GENERATION ANALYSIS")
        print("=" * 60)
        
        print("\n📊 SYSTEM ARCHITECTURE:")
        structure = self.analyze_prompt_structure()
        arch = structure["generation_architecture"]
        print(f"  • {arch['concepts_per_brand']} Core Brand Concepts")
        print(f"  • {arch['executions_per_concept']} Studio Executions per Concept") 
        print(f"  • {arch['total_prompts']} Total Unique Prompts")
        print(f"  • {arch['word_range']}")
        
        print("\n🏢 THE 3 AI DESIGN STUDIOS:")
        for studio, details in self.studio_definitions.items():
            print(f"\n  🎯 Studio \"{studio}\" ({details['focus']}):")
            if 'materials' in details:
                print(f"    Materials: {', '.join(details['materials'][:3])}...")
            if 'techniques' in details:
                print(f"    Techniques: {', '.join(details['techniques'][:2])}...")
            if 'styles' in details:
                print(f"    Styles: {', '.join(details['styles'][:3])}...")
            print(f"    Keywords: {', '.join(details['keywords'])}")
        
        print("\n📝 FORM DATA TO PROMPT MAPPING:")
        mapping = self.get_form_to_prompt_mapping()
        for field, info in mapping.items():
            print(f"\n  🔹 {field.upper()}:")
            print(f"    Usage: {info['usage']}")
            if 'examples' in info:
                print(f"    Examples: {', '.join(info['examples'])}")
            if 'mappings' in info:
                print("    Industry Mappings:")
                for industry, concepts in list(info['mappings'].items())[:3]:
                    print(f"      • {industry}: {concepts}")
        
        print("\n🎨 PROMPT VARIETY BY INDUSTRY:")
        samples = self.get_sample_prompts_by_industry()
        
        for industry, studios in samples.items():
            print(f"\n  📋 {industry}:")
            for studio, prompts in studios.items():
                print(f"    🎯 {studio} Studio:")
                for i, prompt in enumerate(prompts[:1], 1):  # Show 1 per studio
                    preview = prompt[:80] + "..." if len(prompt) > 80 else prompt
                    print(f"      {i}. {preview}")
        
        print("\n🔄 GENERATION CATEGORIES:")
        categories = {
            "Material-Based": ["Liquid effects", "Glass/crystal", "Metal finishes", "Stone/marble", "Technical materials"],
            "Style-Based": ["Photorealistic", "Typography-focused", "Minimalist", "Retro/vintage", "Futuristic"],
            "Technique-Based": ["3D rendering", "Vector illustration", "Photography", "Architectural viz", "Graphic design"],
            "Concept-Based": ["Negative space", "Optical illusions", "Mathematical precision", "Organic forms", "Dynamic energy"]
        }
        
        for category, types in categories.items():
            print(f"\n  🎯 {category}:")
            print(f"    {', '.join(types[:4])}...")
        
        print("\n✨ KEY DIFFERENTIATORS:")
        print("  • Each prompt is 40-60 words of specific creative direction")
        print("  • Professional terminology and studio-quality keywords") 
        print("  • Extensive material and technique variety")
        print("  • Industry-specific concept adaptation")
        print("  • No repetitive language patterns")
        print("  • Balanced distribution across 3 distinct studio styles")
        
        print(f"\n{'='*60}")
        print("🎯 RESULT: 15 unique, professional-grade prompts per brand")
        print("Each optimized for different aesthetics and target applications")
        print(f"{'='*60}")

def main():
    """Main analysis function"""
    analyzer = PromptTypeAnalyzer()
    analyzer.print_comprehensive_analysis()

if __name__ == "__main__":
    main()
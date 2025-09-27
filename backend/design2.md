Perfect. I see it. This is our second style, and it's completely different from the first. This is exactly how we build our library.

Let's call this style **"Cinematic & Symbolic."**

### Analysis of "Cinematic & Symbolic" Style

This style is about creating a single, breathtaking image where the logo feels like a natural, almost magical, element within a photorealistic or hyper-realistic scene.

1.  **Seamless Integration:** This is the most important rule. The logo is not just pasted on top; it *belongs* in the scene. It's affected by the same lighting, atmosphere, and depth of field as the environment around it. It can be glowing, made of stone, or carved into a surface.
2.  **Photorealistic & 3D Backgrounds:** Unlike the graphic backgrounds of the "Retro & Bold" style, these are cinematic, atmospheric, and often photorealistic 3D renders. They evoke a sense of wonder, nature, or technology.
3.  **Minimalist, Powerful Symbols:** The logos themselves are extremely simple, clean, and symbolic. They are often abstract glyphs or simple geometric constructions. The power comes from the contrast between the simple, perfect form of the logo and the complex, textured detail of the environment.
4.  **Dramatic, "Hero" Lighting:** The lighting is the star. It's cinematic, moody, and always tells a story. It might be the golden hour sun casting long shadows, a mysterious glow from within a cave, or the soft light filtering through an ancient ruin.

---

### The Plan: Adding "Cinematic & Symbolic" to our Style Library

Our backend architecture is designed for this. When a user selects "Cinematic & Symbolic" in the UI, the `orchestrator_service` will now instruct the `prompt_engineering_service` to use the new, specialized meta-prompt for this style.

---

### The System Prompt for Gemini: "The Cinematic & Symbolic" Style

Here is the second expert "persona" for Gemini. This meta-prompt is a creative brief specifically for generating logos in this beautiful, integrated style.

**(This will be a new option in our `prompt_engineering_service` to be used when this style is selected.)**

> You are **"Aperture"**, a world-renowned AI concept artist and cinematographer. You specialize in creating breathtaking, cinematic images where powerful, minimalist symbols are seamlessly integrated into hyper-realistic environments. Your work feels like a still from a blockbuster sci-fi or fantasy film.
>
> **YOUR MANDATE:**
> A user wants a logo in your signature **Cinematic & Symbolic** style. You will generate **15 distinct prompts** for Nano Banana (or a similar high-quality text-to-image model) that create a single, cohesive, and awe-inspiring image.
>
> **Brand Information:**
> - Company Name: [Company Name]
> - Industry: [Industry]
> - Description: [Description]
>
> **CRITICAL COMMANDS FOR "CINEMATIC & SYMBOLIC" PROMPTS:**
>
> 1.  **THE LOGO AND SCENE ARE ONE:** The logo must be part of the environment. Command the AI to give the logo texture, light, and physicality that matches the scene.
>     - **Integration Keywords:** `a glowing emblem carved into the rock`, `a symbol formed by natural light filtering through the trees`, `a giant monolithic logo made of stone`, `a logo made of translucent, glowing crystal`.
> 2.  **CREATE CINEMATIC SCENES:** The background is not a backdrop; it's a world.
>     - **Scene Keywords:** `cinematic wide shot`, `hyper-realistic 3D render`, `fantasy landscape`, `ancient ruins overgrown with nature`, `otherworldly alien desert`, `dramatic macro photography`.
> 3.  **MASTERFUL LIGHTING & ATMOSPHERE:** The mood is everything.
>     - **Lighting Keywords:** `volumetric lighting`, `god rays streaming through clouds`, `ethereal glow`, `dramatic rim lighting`, `golden hour`.
>     - **Atmosphere Keywords:** `subtle mist`, `shallow depth of field`, `soft bokeh`, `lens flare`.
> 4.  **THE SYMBOL MUST BE MINIMALIST:** The power comes from contrast. The logo's form must be a simple, clean, powerful glyph or geometric shape.
> 5.  **NEGATIVE PROMPTS:** Use negative prompts to refine the quality, but do not forbid 3D or realism, as that is the goal. Use `--no text, letters, words, typography, people, busy, cluttered`.
>
> **OUTPUT FORMAT:**
> Return a single, valid JSON object: `{"prompts": ["prompt1", ... ,"prompt15"]}`

---

### Example Prompts for "CyberVault" in this Style

1.  `Cinematic wide shot of a massive, brutalist-inspired fortress made of dark, weathered stone, half-buried in a misty arctic landscape. Carved into the main gate is a giant, glowing blue emblem of a minimalist geometric shield. Volumetric lighting, hyper-realistic 3D render, moody atmosphere. --no text, people`
2.  `A hyper-realistic 3D render of a dark, cavernous cave interior. In the center, a monolithic cube-shaped logo made of obsidian glass stands on the ground, with intricate, glowing circuit patterns running through it. Ethereal god rays shine down from an opening in the ceiling. ArtStation, cinematic. --no text, letters`
3.  `Dramatic macro photography of a futuristic, dark metallic surface with intricate geometric patterns. Engraved into the surface is a clean, minimalist logo of a keyhole inside a shield. Subtle red rim lighting catches the edge of the engraving, shallow depth of field. --no text, words`

This gives us a powerful new creative direction to offer users. We are building a truly versatile design platform.

**Your turn, co-founder. Send me the next style.**
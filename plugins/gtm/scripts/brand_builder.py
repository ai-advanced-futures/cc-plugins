from __future__ import annotations


class BrandIdentityBuilder:
    def build(
        self,
        brand_name: str,
        category: str,
        owned_word: str,
        personality_traits: list[str],
        promise: str,
    ) -> dict:
        return {
            "brand_name": brand_name,
            "category": category,
            "owned_word": owned_word,
            "promise": promise,
            "brand_as_product": {"category": category, "scope": [], "attributes": []},
            "brand_as_person": {"personality_traits": personality_traits, "brand_customer_relationship": []},
            "brand_as_symbol": {"visual_imagery": [], "metaphor": "", "heritage": ""},
            "brand_as_organization": {"organizational_values": [], "local_vs_global": ""},
        }


class VoiceGuideGenerator:
    def generate(self, personality_traits: list[str], tone: str, vocabulary_avoid: list[str]) -> dict:
        return {
            "tone": tone,
            "personality_traits": personality_traits,
            "dos": [f"Be {t}" for t in personality_traits],
            "donts": [f"Avoid {w}" for w in vocabulary_avoid],
            "vocabulary_avoid": vocabulary_avoid,
            "example_phrases": [],
        }

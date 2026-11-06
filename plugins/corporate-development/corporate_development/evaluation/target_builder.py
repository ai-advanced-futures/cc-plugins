"""Target statement builder for acquisition criteria."""

from typing import Dict


# Industry type display names
INDUSTRY_TYPES = {
    "saas": "SaaS",
    "ecommerce": "E-commerce",
    "services": "Services",
    "marketplace": "Marketplace",
    "content": "Content/Media",
    "fintech": "FinTech",
    "healthtech": "HealthTech",
    "edtech": "EdTech"
}

# Profile display names
PROFILE_NAMES = {
    "stable_cash": "Stable Cash Flow",
    "growth": "Growth",
    "turnaround": "Turnaround",
    "platform": "Platform"
}


class TargetBuilder:
    """Builder for generating formatted target acquisition statements."""

    @staticmethod
    def generate_statement(params: Dict) -> str:
        """
        Generate a formatted target statement from acquisition criteria.

        Args:
            params: Dictionary containing:
                - industry: Industry type key
                - profile: Opportunity profile key
                - sde_min: Minimum SDE
                - sde_max: Maximum SDE
                - geography: List of geographic regions
                - remote_ok: Whether remote-friendly
                - business_model: Business model type

        Returns:
            Formatted target statement string
        """
        # Format industry and profile
        industry = INDUSTRY_TYPES.get(params["industry"], params["industry"])
        profile = PROFILE_NAMES.get(params["profile"], params["profile"])

        # Format SDE range with thousand separators
        sde_min = f"${params['sde_min']:,}"
        sde_max = f"${params['sde_max']:,}"
        sde_range = f"{sde_min} to {sde_max}"

        # Build limiters
        limiters = []

        # Geography
        if params.get("geography"):
            geo_list = params["geography"]
            if isinstance(geo_list, list):
                geo_text = ", ".join(geo_list)
            else:
                geo_text = geo_list
            limiters.append(f"located in {geo_text}")

        # Remote-friendly
        if params.get("remote_ok"):
            limiters.append("remote-friendly")

        # Business model
        if params.get("business_model"):
            limiters.append(f"{params['business_model']} model")

        # Join limiters
        limiter_text = ", ".join(limiters) if limiters else ""

        # Build statement
        statement = (
            f"I am looking for a {industry} company with {profile} characteristics, "
            f"generating {sde_range} in SDE"
        )

        if limiter_text:
            statement += f", {limiter_text}"

        statement += "."

        return statement

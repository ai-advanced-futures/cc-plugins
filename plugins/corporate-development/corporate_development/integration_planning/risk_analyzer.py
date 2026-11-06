"""RiskAnalyzer for generating integration risks.

This module provides the RiskAnalyzer class which generates integration risks
based on input conditions, including importing critical risks and generating
domain-specific risks with mitigation strategies.
"""

from typing import List
from corporate_development.integration_planning.types import (
    IntegrationPlanningInput,
    Risk,
    Severity,
    Likelihood,
    Impact,
)


class RiskAnalyzer:
    """Generates integration risks based on input conditions.

    This analyzer generates 15-20 integration risks across multiple domains:
    - Team & Leadership
    - Technology
    - Product
    - Customer Success
    - Operations
    - Finance

    Risks include:
    - Critical risks imported from input
    - Conditional risks based on input data (weak team, high tech debt, etc.)
    - Standard integration risks
    """

    def __init__(self):
        """Initialize RiskAnalyzer."""
        pass

    def generate_risks(self, input_data: IntegrationPlanningInput) -> List[Risk]:
        """Generate integration risks based on input conditions.

        Args:
            input_data: Integration planning input with conditions.

        Returns:
            List of 15-20 Risk instances.
        """
        risks = []
        risk_counter = 1

        # Import critical risks from input
        if input_data.critical_risks:
            for critical_risk_desc in input_data.critical_risks:
                risk = self._create_critical_risk(
                    f"R-{risk_counter:03d}",
                    critical_risk_desc
                )
                risks.append(risk)
                risk_counter += 1

        # Generate conditional risks based on input
        risks.extend(self._generate_conditional_risks(input_data, risk_counter))
        risk_counter += len(risks) - len(input_data.critical_risks or [])

        # Generate standard integration risks
        standard_risks = self._generate_standard_risks(risk_counter)
        risks.extend(standard_risks)

        # Ensure we have 15-20 risks
        return risks[:20]

    def _create_critical_risk(self, risk_id: str, description: str) -> Risk:
        """Create a risk from critical risk description.

        Args:
            risk_id: Unique risk identifier
            description: Risk description

        Returns:
            Risk instance with high/critical severity
        """
        # Determine domain based on keywords
        domain = self._determine_domain_from_description(description)

        # Determine appropriate owner based on domain
        owner = self._get_owner_for_domain(domain)

        return Risk(
            id=risk_id,
            domain=domain,
            description=description,
            likelihood=Likelihood.HIGH,
            impact=Impact.HIGH,
            severity=Severity.CRITICAL,
            mitigation_strategy=self._generate_mitigation_strategy(description),
            owner=owner
        )

    def _generate_conditional_risks(
        self,
        input_data: IntegrationPlanningInput,
        start_id: int
    ) -> List[Risk]:
        """Generate risks based on input conditions.

        Args:
            input_data: Integration planning input
            start_id: Starting risk ID number

        Returns:
            List of conditional risks
        """
        risks = []
        counter = start_id

        # Weak team risks
        if input_data.team_strength and input_data.team_strength.lower() == "weak":
            risks.extend([
                Risk(
                    id=f"R-{counter:03d}",
                    domain="Team & Leadership",
                    description="High attrition risk due to weak team morale and uncertainty",
                    likelihood=Likelihood.HIGH,
                    impact=Impact.HIGH,
                    severity=Severity.HIGH,
                    mitigation_strategy="Implement retention bonuses, accelerate communication cadence, conduct 1-on-1s with key employees within first week",
                    owner="CHRO"
                ),
                Risk(
                    id=f"R-{counter+1:03d}",
                    domain="Team & Leadership",
                    description="Leadership vacuum if existing managers depart during transition",
                    likelihood=Likelihood.MEDIUM,
                    impact=Impact.HIGH,
                    severity=Severity.HIGH,
                    mitigation_strategy="Identify critical roles, prepare interim leadership plan, cross-train existing team members",
                    owner="CEO"
                ),
            ])
            counter += 2

        # High tech debt risks
        if input_data.tech_debt_level and input_data.tech_debt_level.lower() == "high":
            risks.extend([
                Risk(
                    id=f"R-{counter:03d}",
                    domain="Technology",
                    description="System instability during integration due to high technical debt",
                    likelihood=Likelihood.HIGH,
                    impact=Impact.HIGH,
                    severity=Severity.CRITICAL,
                    mitigation_strategy="Conduct comprehensive technical audit, establish code freeze periods, implement staged rollout plan",
                    owner="CTO"
                ),
                Risk(
                    id=f"R-{counter+1:03d}",
                    domain="Technology",
                    description="Integration delays due to undocumented legacy systems",
                    likelihood=Likelihood.MEDIUM,
                    impact=Impact.MEDIUM,
                    severity=Severity.MEDIUM,
                    mitigation_strategy="Allocate additional time for system documentation, engage original developers if available, consider parallel systems approach",
                    owner="VP Engineering"
                ),
            ])
            counter += 2

        # Low operational health risks
        if input_data.operational_health_score and input_data.operational_health_score < 50:
            risks.append(
                Risk(
                    id=f"R-{counter:03d}",
                    domain="Operations",
                    description="Operational disruption during integration due to poor existing processes",
                    likelihood=Likelihood.HIGH,
                    impact=Impact.MEDIUM,
                    severity=Severity.HIGH,
                    mitigation_strategy="Map critical processes early, implement process improvement initiatives, establish clear escalation paths",
                    owner="COO"
                )
            )
            counter += 1

        # Low financial health risks
        if input_data.financial_health_score and input_data.financial_health_score < 60:
            risks.append(
                Risk(
                    id=f"R-{counter:03d}",
                    domain="Finance",
                    description="Cash flow challenges impacting integration investment",
                    likelihood=Likelihood.MEDIUM,
                    impact=Impact.HIGH,
                    severity=Severity.HIGH,
                    mitigation_strategy="Secure additional working capital, prioritize revenue-generating activities, implement strict cost controls",
                    owner="CFO"
                )
            )
            counter += 1

        return risks

    def _generate_standard_risks(self, start_id: int) -> List[Risk]:
        """Generate standard integration risks.

        Args:
            start_id: Starting risk ID number

        Returns:
            List of standard risks
        """
        risks = [
            Risk(
                id=f"R-{start_id:03d}",
                domain="Customer Success",
                description="Customer churn during ownership transition due to uncertainty",
                likelihood=Likelihood.MEDIUM,
                impact=Impact.HIGH,
                severity=Severity.HIGH,
                mitigation_strategy="Execute customer communication plan immediately, assign dedicated customer success managers, offer incentives for contract renewals",
                owner="VP Customer Success"
            ),
            Risk(
                id=f"R-{start_id+1:03d}",
                domain="Product",
                description="Product roadmap conflicts between acquirer and target vision",
                likelihood=Likelihood.MEDIUM,
                impact=Impact.MEDIUM,
                severity=Severity.MEDIUM,
                mitigation_strategy="Conduct joint roadmap session within first 30 days, establish product council, align on 12-month priorities",
                owner="CPO"
            ),
            Risk(
                id=f"R-{start_id+2:03d}",
                domain="Technology",
                description="Security vulnerabilities exposed during systems integration",
                likelihood=Likelihood.MEDIUM,
                impact=Impact.HIGH,
                severity=Severity.HIGH,
                mitigation_strategy="Conduct security audit before integration, implement security hardening, establish incident response plan",
                owner="CISO"
            ),
            Risk(
                id=f"R-{start_id+3:03d}",
                domain="Team & Leadership",
                description="Cultural clash between organizations leading to reduced productivity",
                likelihood=Likelihood.MEDIUM,
                impact=Impact.MEDIUM,
                severity=Severity.MEDIUM,
                mitigation_strategy="Conduct culture assessment, facilitate joint team-building activities, establish shared values early",
                owner="CHRO"
            ),
            Risk(
                id=f"R-{start_id+4:03d}",
                domain="Finance",
                description="Integration costs exceeding budget projections",
                likelihood=Likelihood.MEDIUM,
                impact=Impact.MEDIUM,
                severity=Severity.MEDIUM,
                mitigation_strategy="Establish detailed integration budget with 20% contingency, implement weekly spend tracking, approve all major expenses",
                owner="CFO"
            ),
            Risk(
                id=f"R-{start_id+5:03d}",
                domain="Operations",
                description="Process inefficiencies during consolidation of operations",
                likelihood=Likelihood.MEDIUM,
                impact=Impact.LOW,
                severity=Severity.LOW,
                mitigation_strategy="Document and standardize processes before consolidation, implement gradual transition, monitor key metrics daily",
                owner="COO"
            ),
            Risk(
                id=f"R-{start_id+6:03d}",
                domain="Customer Success",
                description="Support quality degradation during team integration",
                likelihood=Likelihood.LOW,
                impact=Impact.MEDIUM,
                severity=Severity.MEDIUM,
                mitigation_strategy="Maintain separate support teams initially, cross-train gradually, monitor support metrics closely",
                owner="VP Customer Success"
            ),
            Risk(
                id=f"R-{start_id+7:03d}",
                domain="Product",
                description="Feature development slowdown during integration period",
                likelihood=Likelihood.HIGH,
                impact=Impact.MEDIUM,
                severity=Severity.MEDIUM,
                mitigation_strategy="Set realistic expectations with stakeholders, maintain separate development streams initially, focus on critical features only",
                owner="VP Engineering"
            ),
            Risk(
                id=f"R-{start_id+8:03d}",
                domain="Technology",
                description="Data migration failures or data loss during system consolidation",
                likelihood=Likelihood.LOW,
                impact=Impact.HIGH,
                severity=Severity.HIGH,
                mitigation_strategy="Implement comprehensive backup strategy, conduct dry-run migrations, maintain parallel systems during transition",
                owner="CTO"
            ),
            Risk(
                id=f"R-{start_id+9:03d}",
                domain="Team & Leadership",
                description="Key knowledge loss if documentation is inadequate",
                likelihood=Likelihood.MEDIUM,
                impact=Impact.MEDIUM,
                severity=Severity.MEDIUM,
                mitigation_strategy="Initiate knowledge transfer sessions immediately, implement documentation sprints, record key processes and decisions",
                owner="VP Operations"
            ),
            Risk(
                id=f"R-{start_id+10:03d}",
                domain="Finance",
                description="Revenue recognition complexities during financial system integration",
                likelihood=Likelihood.MEDIUM,
                impact=Impact.MEDIUM,
                severity=Severity.MEDIUM,
                mitigation_strategy="Engage accounting firm early, document revenue policies, implement dual tracking during transition",
                owner="Controller"
            ),
            Risk(
                id=f"R-{start_id+11:03d}",
                domain="Operations",
                description="Vendor contract renegotiation failures impacting cost synergies",
                likelihood=Likelihood.LOW,
                impact=Impact.LOW,
                severity=Severity.LOW,
                mitigation_strategy="Review all vendor contracts early, prioritize high-value renegotiations, maintain relationships with critical vendors",
                owner="Procurement Manager"
            ),
            Risk(
                id=f"R-{start_id+12:03d}",
                domain="Team & Leadership",
                description="Communication breakdown between distributed teams during integration",
                likelihood=Likelihood.MEDIUM,
                impact=Impact.MEDIUM,
                severity=Severity.MEDIUM,
                mitigation_strategy="Establish clear communication protocols, implement collaboration tools, schedule regular all-hands meetings",
                owner="VP Communications"
            ),
            Risk(
                id=f"R-{start_id+13:03d}",
                domain="Product",
                description="Integration disrupting product quality and increasing bug rate",
                likelihood=Likelihood.MEDIUM,
                impact=Impact.MEDIUM,
                severity=Severity.MEDIUM,
                mitigation_strategy="Increase QA resources temporarily, implement rigorous testing protocols, establish bug triage process",
                owner="VP Engineering"
            ),
            Risk(
                id=f"R-{start_id+14:03d}",
                domain="Customer Success",
                description="Loss of customer trust due to service disruptions during integration",
                likelihood=Likelihood.LOW,
                impact=Impact.HIGH,
                severity=Severity.MEDIUM,
                mitigation_strategy="Maintain service level agreements, provide proactive status updates, offer compensation for any disruptions",
                owner="VP Customer Success"
            ),
        ]

        return risks

    def _determine_domain_from_description(self, description: str) -> str:
        """Determine risk domain based on description keywords.

        Args:
            description: Risk description

        Returns:
            Domain name
        """
        desc_lower = description.lower()

        if any(keyword in desc_lower for keyword in ["team", "employee", "staff", "talent", "culture", "leadership"]):
            return "Team & Leadership"
        elif any(keyword in desc_lower for keyword in ["technology", "tech", "system", "infrastructure", "security", "technical"]):
            return "Technology"
        elif any(keyword in desc_lower for keyword in ["product", "feature", "roadmap", "development"]):
            return "Product"
        elif any(keyword in desc_lower for keyword in ["customer", "client", "support", "churn"]):
            return "Customer Success"
        elif any(keyword in desc_lower for keyword in ["operation", "process", "vendor", "supply"]):
            return "Operations"
        elif any(keyword in desc_lower for keyword in ["financial", "revenue", "cost", "budget", "cash"]):
            return "Finance"
        else:
            return "General"

    def _get_owner_for_domain(self, domain: str) -> str:
        """Get appropriate owner for a risk domain.

        Args:
            domain: Risk domain

        Returns:
            Owner role/title
        """
        owner_map = {
            "Team & Leadership": "CHRO",
            "Technology": "CTO",
            "Product": "CPO",
            "Customer Success": "VP Customer Success",
            "Operations": "COO",
            "Finance": "CFO",
            "General": "CEO"
        }
        return owner_map.get(domain, "Integration Lead")

    def _generate_mitigation_strategy(self, risk_description: str) -> str:
        """Generate mitigation strategy based on risk description.

        Args:
            risk_description: Description of the risk

        Returns:
            Mitigation strategy
        """
        desc_lower = risk_description.lower()

        # Provide contextual mitigation based on risk type
        if "leave" in desc_lower or "depart" in desc_lower or "attrition" in desc_lower:
            return "Implement retention bonuses and incentives, conduct regular 1-on-1s, create clear career development paths, expedite key hires"

        if "customer" in desc_lower or "client" in desc_lower:
            return "Execute proactive customer communication plan, assign dedicated account managers, offer service level guarantees, conduct customer satisfaction surveys"

        if "security" in desc_lower or "vulnerability" in desc_lower:
            return "Conduct comprehensive security audit, implement security hardening measures, establish incident response procedures, engage third-party security assessment"

        if "system" in desc_lower or "technical" in desc_lower or "technology" in desc_lower:
            return "Perform detailed technical assessment, create integration architecture plan, implement staged rollout approach, maintain rollback capabilities"

        if "financial" in desc_lower or "budget" in desc_lower or "cost" in desc_lower:
            return "Establish detailed budget with contingency, implement weekly financial tracking, require approval for significant expenditures, prioritize revenue-generating activities"

        # Generic mitigation
        return "Conduct thorough assessment, develop detailed action plan, assign clear ownership, establish monitoring and reporting cadence, maintain contingency plans"

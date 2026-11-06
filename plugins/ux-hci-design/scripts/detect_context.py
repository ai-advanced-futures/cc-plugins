#!/usr/bin/env python3
"""
Context Detection for UX/HCI Design Plugin

Auto-detects project context from codebase to enable context-aware
UX evaluation and framework prioritization.

Detection signals:
- package.json: dependencies, frameworks, platforms
- Cargo.toml, go.mod, requirements.txt: language/framework detection
- Directory structure: mobile, web, desktop patterns
- Code patterns: accessibility, AI/ML usage
- Configuration files: platform targets, build configs
"""

import json
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional


@dataclass
class DetectionSignal:
    """A signal detected from the codebase."""
    signal: str
    source: str
    inference: str
    confidence: str = "medium"  # high, medium, low


@dataclass
class DetectedContext:
    """Detected project context with confidence scores."""
    project_type: str = "web-app"
    domain: str = "consumer"
    ai_intensity: str = "none"
    accessibility_requirements: str = "required"
    platforms: List[str] = field(default_factory=lambda: ["web"])
    user_expertise: str = "mixed"
    signals: List[DetectionSignal] = field(default_factory=list)
    overall_confidence: str = "medium"

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "type": self.project_type,
            "domain": self.domain,
            "ai_intensity": self.ai_intensity,
            "accessibility_requirements": self.accessibility_requirements,
            "platforms": self.platforms,
            "user_expertise": self.user_expertise
        }


class ContextDetector:
    """Detects project context from codebase analysis."""

    def __init__(self, project_root: Path):
        """
        Initialize detector with project root path.

        Args:
            project_root: Root directory of the project to analyze
        """
        self.project_root = Path(project_root)
        self.signals: List[DetectionSignal] = []
        self.context = DetectedContext()

    def detect(self) -> DetectedContext:
        """
        Run full context detection.

        Returns:
            DetectedContext with all detected signals
        """
        self.signals = []

        # Run all detection methods
        self._detect_from_package_json()
        self._detect_from_cargo_toml()
        self._detect_from_go_mod()
        self._detect_from_requirements_txt()
        self._detect_from_directory_structure()
        self._detect_from_config_files()
        self._detect_accessibility_patterns()
        self._detect_ai_patterns()

        # Synthesize signals into context
        self._synthesize_context()

        self.context.signals = self.signals
        return self.context

    def _detect_from_package_json(self) -> None:
        """Detect context from package.json."""
        package_json_path = self.project_root / "package.json"
        if not package_json_path.exists():
            return

        try:
            with open(package_json_path, 'r', encoding='utf-8') as f:
                package = json.load(f)
        except (json.JSONDecodeError, IOError):
            return

        deps = {}
        deps.update(package.get('dependencies', {}))
        deps.update(package.get('devDependencies', {}))
        dep_names = set(deps.keys())

        # Detect frameworks
        if 'react' in dep_names or 'react-dom' in dep_names:
            self.signals.append(DetectionSignal(
                signal="React framework detected",
                source="package.json",
                inference="Web application (React)",
                confidence="high"
            ))

        if 'next' in dep_names:
            self.signals.append(DetectionSignal(
                signal="Next.js framework detected",
                source="package.json",
                inference="Web application (Next.js)",
                confidence="high"
            ))

        if 'vue' in dep_names:
            self.signals.append(DetectionSignal(
                signal="Vue.js framework detected",
                source="package.json",
                inference="Web application (Vue.js)",
                confidence="high"
            ))

        if 'angular' in dep_names or '@angular/core' in dep_names:
            self.signals.append(DetectionSignal(
                signal="Angular framework detected",
                source="package.json",
                inference="Web application (Angular)",
                confidence="high"
            ))

        if 'svelte' in dep_names:
            self.signals.append(DetectionSignal(
                signal="Svelte framework detected",
                source="package.json",
                inference="Web application (Svelte)",
                confidence="high"
            ))

        # Detect mobile
        if 'react-native' in dep_names:
            self.signals.append(DetectionSignal(
                signal="React Native detected",
                source="package.json",
                inference="Mobile application (React Native)",
                confidence="high"
            ))

        if 'expo' in dep_names:
            self.signals.append(DetectionSignal(
                signal="Expo detected",
                source="package.json",
                inference="Mobile application (Expo)",
                confidence="high"
            ))

        # Detect Electron (desktop)
        if 'electron' in dep_names:
            self.signals.append(DetectionSignal(
                signal="Electron detected",
                source="package.json",
                inference="Desktop application (Electron)",
                confidence="high"
            ))

        # Detect AI/ML libraries
        ai_packages = [
            '@anthropic-ai/sdk', 'anthropic', 'openai', '@openai/api',
            'langchain', '@langchain/core', 'ai', '@ai-sdk/core',
            'transformers', 'tensorflow', '@tensorflow/tfjs',
            'llamaindex', 'cohere-ai', 'replicate'
        ]
        detected_ai = [pkg for pkg in ai_packages if pkg in dep_names]
        if detected_ai:
            self.signals.append(DetectionSignal(
                signal=f"AI/ML packages detected: {', '.join(detected_ai)}",
                source="package.json",
                inference="AI-heavy application",
                confidence="high"
            ))

        # Detect accessibility libraries
        a11y_packages = [
            '@axe-core/react', 'axe-core', 'react-aria', '@react-aria/utils',
            'focus-trap', 'focus-trap-react', '@radix-ui/react-focus-scope',
            'ally.js', 'a11y-dialog'
        ]
        detected_a11y = [pkg for pkg in a11y_packages if pkg in dep_names]
        if detected_a11y:
            self.signals.append(DetectionSignal(
                signal=f"Accessibility packages detected: {', '.join(detected_a11y)}",
                source="package.json",
                inference="Accessibility-aware application",
                confidence="high"
            ))

        # Detect testing libraries (indicates quality focus)
        test_packages = ['jest', 'vitest', '@testing-library/react', 'cypress', 'playwright']
        detected_tests = [pkg for pkg in test_packages if pkg in dep_names]
        if detected_tests:
            self.signals.append(DetectionSignal(
                signal=f"Testing frameworks detected: {', '.join(detected_tests)}",
                source="package.json",
                inference="Quality-focused development",
                confidence="medium"
            ))

    def _detect_from_cargo_toml(self) -> None:
        """Detect context from Cargo.toml (Rust projects)."""
        cargo_path = self.project_root / "Cargo.toml"
        if not cargo_path.exists():
            return

        try:
            with open(cargo_path, 'r', encoding='utf-8') as f:
                content = f.read()
        except IOError:
            return

        self.signals.append(DetectionSignal(
            signal="Rust project detected",
            source="Cargo.toml",
            inference="Systems/performance-focused application",
            confidence="high"
        ))

        # Check for GUI frameworks
        if 'tauri' in content.lower():
            self.signals.append(DetectionSignal(
                signal="Tauri detected",
                source="Cargo.toml",
                inference="Desktop application (Tauri)",
                confidence="high"
            ))

        if 'egui' in content.lower() or 'iced' in content.lower():
            self.signals.append(DetectionSignal(
                signal="Rust GUI framework detected",
                source="Cargo.toml",
                inference="Desktop application (Rust GUI)",
                confidence="high"
            ))

    def _detect_from_go_mod(self) -> None:
        """Detect context from go.mod (Go projects)."""
        go_mod_path = self.project_root / "go.mod"
        if not go_mod_path.exists():
            return

        self.signals.append(DetectionSignal(
            signal="Go project detected",
            source="go.mod",
            inference="Backend/systems application",
            confidence="high"
        ))

    def _detect_from_requirements_txt(self) -> None:
        """Detect context from requirements.txt (Python projects)."""
        req_path = self.project_root / "requirements.txt"
        pyproject_path = self.project_root / "pyproject.toml"

        content = ""
        source = ""

        if req_path.exists():
            try:
                with open(req_path, 'r', encoding='utf-8') as f:
                    content = f.read().lower()
                    source = "requirements.txt"
            except IOError:
                pass
        elif pyproject_path.exists():
            try:
                with open(pyproject_path, 'r', encoding='utf-8') as f:
                    content = f.read().lower()
                    source = "pyproject.toml"
            except IOError:
                pass

        if not content:
            return

        # Detect web frameworks
        if 'django' in content or 'flask' in content or 'fastapi' in content:
            self.signals.append(DetectionSignal(
                signal="Python web framework detected",
                source=source,
                inference="Web application (Python backend)",
                confidence="high"
            ))

        # Detect AI/ML libraries
        ai_libs = ['openai', 'anthropic', 'langchain', 'transformers', 'torch', 'tensorflow']
        detected_ai = [lib for lib in ai_libs if lib in content]
        if detected_ai:
            self.signals.append(DetectionSignal(
                signal=f"Python AI/ML libraries detected: {', '.join(detected_ai)}",
                source=source,
                inference="AI-heavy application",
                confidence="high"
            ))

    def _detect_from_directory_structure(self) -> None:
        """Detect context from directory structure."""
        # Check for mobile directories
        if (self.project_root / "ios").exists():
            self.signals.append(DetectionSignal(
                signal="ios/ directory detected",
                source="directory structure",
                inference="iOS mobile application",
                confidence="high"
            ))

        if (self.project_root / "android").exists():
            self.signals.append(DetectionSignal(
                signal="android/ directory detected",
                source="directory structure",
                inference="Android mobile application",
                confidence="high"
            ))

        # Check for common web patterns
        web_dirs = ['public', 'static', 'src/pages', 'src/components', 'app']
        for web_dir in web_dirs:
            if (self.project_root / web_dir).exists():
                self.signals.append(DetectionSignal(
                    signal=f"{web_dir}/ directory detected",
                    source="directory structure",
                    inference="Web application structure",
                    confidence="medium"
                ))
                break

        # Check for API patterns
        api_dirs = ['api', 'src/api', 'routes', 'endpoints']
        for api_dir in api_dirs:
            if (self.project_root / api_dir).exists():
                self.signals.append(DetectionSignal(
                    signal=f"{api_dir}/ directory detected",
                    source="directory structure",
                    inference="API/Backend service",
                    confidence="medium"
                ))
                break

    def _detect_from_config_files(self) -> None:
        """Detect context from various config files."""
        # Check for TypeScript (enterprise indicator)
        if (self.project_root / "tsconfig.json").exists():
            self.signals.append(DetectionSignal(
                signal="TypeScript configuration detected",
                source="tsconfig.json",
                inference="Type-safe, potentially enterprise application",
                confidence="medium"
            ))

        # Check for Docker (deployment/production focus)
        if (self.project_root / "Dockerfile").exists() or (self.project_root / "docker-compose.yml").exists():
            self.signals.append(DetectionSignal(
                signal="Docker configuration detected",
                source="Dockerfile/docker-compose.yml",
                inference="Production-ready deployment",
                confidence="medium"
            ))

        # Check for Kubernetes
        if (self.project_root / "k8s").exists() or (self.project_root / "kubernetes").exists():
            self.signals.append(DetectionSignal(
                signal="Kubernetes configuration detected",
                source="k8s/ directory",
                inference="Enterprise-scale deployment",
                confidence="high"
            ))

    def _detect_accessibility_patterns(self) -> None:
        """Detect accessibility patterns in code."""
        # Look for ARIA patterns in common locations
        search_patterns = [
            ('aria-', 'ARIA attributes'),
            ('role=', 'ARIA roles'),
            ('tabindex', 'Keyboard navigation'),
            ('sr-only', 'Screen reader support'),
            ('visually-hidden', 'Screen reader support'),
        ]

        src_dirs = ['src', 'app', 'components', 'pages']
        for src_dir in src_dirs:
            src_path = self.project_root / src_dir
            if not src_path.exists():
                continue

            for pattern, description in search_patterns:
                # Sample a few files to check for patterns
                for ext in ['*.tsx', '*.jsx', '*.vue', '*.svelte', '*.html']:
                    files = list(src_path.rglob(ext))[:5]  # Sample first 5 files
                    for file_path in files:
                        try:
                            with open(file_path, 'r', encoding='utf-8') as f:
                                content = f.read()
                                if pattern in content:
                                    self.signals.append(DetectionSignal(
                                        signal=f"{description} found in code",
                                        source=str(file_path.relative_to(self.project_root)),
                                        inference="Accessibility-conscious implementation",
                                        confidence="high"
                                    ))
                                    return  # One signal is enough

                        except (IOError, UnicodeDecodeError):
                            continue

    def _detect_ai_patterns(self) -> None:
        """Detect AI/ML usage patterns in code."""
        ai_patterns = [
            ('openai', 'OpenAI API usage'),
            ('anthropic', 'Anthropic API usage'),
            ('claude', 'Claude AI usage'),
            ('gpt-', 'GPT model usage'),
            ('langchain', 'LangChain framework'),
            ('embedding', 'Embedding/vector usage'),
            ('llm', 'LLM integration'),
            ('completion', 'AI completion'),
            ('chat.completions', 'Chat API usage'),
        ]

        src_dirs = ['src', 'app', 'lib', 'services', 'api']
        for src_dir in src_dirs:
            src_path = self.project_root / src_dir
            if not src_path.exists():
                continue

            for pattern, description in ai_patterns:
                for ext in ['*.ts', '*.tsx', '*.js', '*.jsx', '*.py']:
                    files = list(src_path.rglob(ext))[:10]
                    for file_path in files:
                        try:
                            with open(file_path, 'r', encoding='utf-8') as f:
                                content = f.read().lower()
                                if pattern in content:
                                    self.signals.append(DetectionSignal(
                                        signal=f"{description} detected",
                                        source=str(file_path.relative_to(self.project_root)),
                                        inference="AI-integrated application",
                                        confidence="high"
                                    ))
                                    return  # One signal is enough
                        except (IOError, UnicodeDecodeError):
                            continue

    def _synthesize_context(self) -> None:
        """Synthesize detected signals into project context."""
        # Count signals by category
        web_signals = sum(1 for s in self.signals if 'web' in s.inference.lower())
        mobile_signals = sum(1 for s in self.signals if 'mobile' in s.inference.lower())
        desktop_signals = sum(1 for s in self.signals if 'desktop' in s.inference.lower())
        ai_signals = sum(1 for s in self.signals if 'ai' in s.inference.lower())
        a11y_signals = sum(1 for s in self.signals if 'accessibility' in s.inference.lower())
        enterprise_signals = sum(1 for s in self.signals if 'enterprise' in s.inference.lower())

        # Determine project type
        if mobile_signals > 0 and web_signals > 0:
            self.context.project_type = "mixed"
            self.context.platforms = ["web", "ios", "android"]
        elif mobile_signals > 0:
            self.context.project_type = "mobile-app"
            self.context.platforms = []
            if any('ios' in s.inference.lower() for s in self.signals):
                self.context.platforms.append("ios")
            if any('android' in s.inference.lower() for s in self.signals):
                self.context.platforms.append("android")
            if not self.context.platforms:
                self.context.platforms = ["ios", "android"]
        elif desktop_signals > 0:
            self.context.project_type = "desktop-app"
            self.context.platforms = ["windows", "macos", "linux"]
        elif enterprise_signals > 0:
            self.context.project_type = "enterprise"
            self.context.platforms = ["web"]
        else:
            self.context.project_type = "web-app"
            self.context.platforms = ["web"]

        # Determine AI intensity
        if ai_signals >= 3:
            self.context.ai_intensity = "core"
        elif ai_signals >= 2:
            self.context.ai_intensity = "heavy"
        elif ai_signals >= 1:
            self.context.ai_intensity = "moderate"
        else:
            self.context.ai_intensity = "none"

        # Determine accessibility requirements
        if a11y_signals >= 2:
            self.context.accessibility_requirements = "critical"
        elif a11y_signals >= 1:
            self.context.accessibility_requirements = "required"
        else:
            self.context.accessibility_requirements = "required"  # Default to required

        # Determine domain (harder to detect, default to consumer)
        if enterprise_signals > 0:
            self.context.domain = "b2b"
        else:
            self.context.domain = "consumer"

        # Calculate overall confidence
        high_confidence = sum(1 for s in self.signals if s.confidence == "high")
        total_signals = len(self.signals)

        if total_signals == 0:
            self.context.overall_confidence = "low"
        elif high_confidence / total_signals > 0.7:
            self.context.overall_confidence = "high"
        elif high_confidence / total_signals > 0.4:
            self.context.overall_confidence = "medium"
        else:
            self.context.overall_confidence = "low"


def get_weighting_profile(context: DetectedContext) -> str:
    """
    Determine the appropriate weighting profile based on context.

    Args:
        context: Detected project context

    Returns:
        Recommended weighting profile name
    """
    if context.ai_intensity in ['heavy', 'core']:
        return "ai-heavy"
    elif context.accessibility_requirements == 'critical':
        return "accessibility-first"
    elif context.project_type == 'mobile-app':
        return "mobile-first"
    elif context.project_type == 'enterprise':
        return "enterprise"
    else:
        return "balanced"


def get_priority_frameworks(context: DetectedContext) -> List[str]:
    """
    Determine priority frameworks based on context.

    Args:
        context: Detected project context

    Returns:
        Ordered list of framework priorities
    """
    if context.ai_intensity in ['heavy', 'core']:
        return ["ai-hci", "nielsen", "wcag", "norman", "rams"]
    elif context.accessibility_requirements == 'critical':
        return ["wcag", "nielsen", "norman", "rams", "ai-hci"]
    elif context.project_type == 'mobile-app':
        return ["nielsen", "norman", "wcag", "rams", "ai-hci"]
    else:
        return ["nielsen", "wcag", "norman", "rams", "ai-hci"]


def generate_config(project_root: Path, project_name: Optional[str] = None) -> Dict[str, Any]:
    """
    Generate a complete .ux-config.json configuration.

    Args:
        project_root: Root directory of the project
        project_name: Optional project name

    Returns:
        Configuration dictionary ready to be saved as JSON
    """
    detector = ContextDetector(project_root)
    context = detector.detect()

    weighting_profile = get_weighting_profile(context)
    priority_frameworks = get_priority_frameworks(context)

    config = {
        "schema_version": "1.0",
        "project_context": context.to_dict(),
        "weighting_profile": weighting_profile,
        "priority_frameworks": priority_frameworks,
        "detection_sources": {
            "auto_detected": True,
            "detected_at": datetime.utcnow().isoformat() + "Z",
            "detection_confidence": context.overall_confidence,
            "detected_signals": [
                {
                    "signal": s.signal,
                    "source": s.source,
                    "inference": s.inference
                }
                for s in context.signals
            ],
            "user_confirmed": False
        },
        "metadata": {
            "created_at": datetime.utcnow().isoformat() + "Z",
            "created_by": "ux-hci-design-plugin"
        }
    }

    if project_name:
        config["metadata"]["project_name"] = project_name

    return config


def save_config(project_root: Path, config: Dict[str, Any]) -> Path:
    """
    Save configuration to .ux-config.json.

    Args:
        project_root: Root directory of the project
        config: Configuration dictionary

    Returns:
        Path to saved config file
    """
    config_path = project_root / ".ux-config.json"
    with open(config_path, 'w', encoding='utf-8') as f:
        json.dump(config, f, indent=2)
    return config_path


def load_config(project_root: Path) -> Optional[Dict[str, Any]]:
    """
    Load existing configuration from .ux-config.json.

    Args:
        project_root: Root directory of the project

    Returns:
        Configuration dictionary or None if not found
    """
    config_path = project_root / ".ux-config.json"
    if not config_path.exists():
        return None

    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError):
        return None


def main():
    """CLI entry point for context detection."""
    import argparse

    parser = argparse.ArgumentParser(
        description='Detect project context for UX/HCI design workflows',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Detect context in current directory
  python detect_context.py

  # Detect context in specific directory
  python detect_context.py --project /path/to/project

  # Generate and save config
  python detect_context.py --save

  # Show detailed signals
  python detect_context.py --verbose
        """
    )
    parser.add_argument(
        '--project', '-p',
        type=Path,
        default=Path.cwd(),
        help='Project root directory (default: current directory)'
    )
    parser.add_argument(
        '--save', '-s',
        action='store_true',
        help='Save config to .ux-config.json'
    )
    parser.add_argument(
        '--verbose', '-v',
        action='store_true',
        help='Show detailed detection signals'
    )
    parser.add_argument(
        '--name', '-n',
        type=str,
        help='Project name for metadata'
    )

    args = parser.parse_args()

    print(f"Detecting project context in: {args.project}")
    print("=" * 60)

    config = generate_config(args.project, args.name)

    print("\nDetected Context:")
    print("-" * 40)
    ctx = config["project_context"]
    print(f"  Type: {ctx['type']}")
    print(f"  Domain: {ctx['domain']}")
    print(f"  AI Intensity: {ctx['ai_intensity']}")
    print(f"  Accessibility: {ctx['accessibility_requirements']}")
    print(f"  Platforms: {', '.join(ctx['platforms'])}")

    print(f"\nWeighting Profile: {config['weighting_profile']}")
    print(f"Priority Frameworks: {', '.join(config['priority_frameworks'])}")
    print(f"Detection Confidence: {config['detection_sources']['detection_confidence']}")

    if args.verbose:
        print("\nDetection Signals:")
        print("-" * 40)
        for signal in config["detection_sources"]["detected_signals"]:
            print(f"  [{signal['source']}]")
            print(f"    Signal: {signal['signal']}")
            print(f"    Inference: {signal['inference']}")
            print()

    if args.save:
        config_path = save_config(args.project, config)
        print(f"\nConfig saved to: {config_path}")
        print("Run `/ux-design` to confirm or modify this context.")

    return 0


if __name__ == '__main__':
    import sys
    sys.exit(main())

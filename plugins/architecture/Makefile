TIER ?= registration

.PHONY: test itest

test:
	ADR_REQUIRE_LINKML=1 uv run --with-requirements requirements-dev.txt python -m pytest tests -q -p no:cacheprovider
	ADR_REQUIRE_LINKML=1 uv run --with-requirements requirements-dev.txt python -m pytest templates/verbatim/tests -q -p no:cacheprovider

itest:
	@test "$(ARCHITECTURE_ITEST)" = "1" || { printf '%s\n' 'Set ARCHITECTURE_ITEST=1 to run live checks.'; exit 2; }
	@case "$(TIER)" in registration|acceptance|interactive|all) ;; *) printf '%s\n' 'TIER must be registration, acceptance, interactive, or all.'; exit 2 ;; esac
	@case "$(TIER)" in interactive|all) test "$(ARCHITECTURE_INTERACTIVE_BASH)" = "1" || { printf '%s\n' 'Set ARCHITECTURE_INTERACTIVE_BASH=1 to permit Bash in the isolated interactive fixture.'; exit 2; } ;; esac
	uv run --with-requirements requirements-dev.txt python -m pytest tests/integration -m 'integration$(if $(filter all,$(TIER)),, and $(TIER))' -rs --tb=short

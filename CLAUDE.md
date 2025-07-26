# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Cost comparison simulator for AWS Lambda vs Virtual Machine deployments to identify break-even points.

## Current Status

✅ **PROJECT COMPLETED** - Full production-ready application with comprehensive testing and documentation.

- ✅ Flask backend with REST API (88% test coverage, 133 tests)
- ✅ Interactive web interface with Chart.js visualization  
- ✅ Multi-cloud cost comparison (6 providers: AWS Lambda/EC2, Google Cloud, Azure, OCI, Sakura Cloud)
- ✅ Advanced features: egress costs, internet transfer ratios, CSV export, currency conversion
- ✅ Docker containerization and production deployment ready

**Total Implementation**: 10 PBIs, 39 story points, 100% complete.
See `Design/Overview.md` for specifications and `/ref/` directory for comprehensive documentation.

## Development Guidelines

### When implementing:
1. Follow the design specifications in `Design/Overview.md`
2. Use Python for backend implementation (managed via mise)
3. Create web-based interface for localhost
4. Implement proper project structure with source directories
5. Use mise for environment and dependency management
6. Follow t_wada TDD principles with pytest framework

### Environment Setup:
- Use `make setup` for complete initial setup (recommended)
- Use `mise install` for Python environment setup
- Use `mise run install` for dependency installation
- **Security Setup**: Create `.mise.local.toml` from `.mise.local.toml.example` with secure keys

### Daily Development Commands:
- Use `make test` (or `make t`) for running tests with coverage
- Use `make lint` (or `make l`) for code quality checks
- Use `make format` (or `make f`) for code formatting
- Use `make dev` for development server
- Use `make check` for all checks before commit
- Use `make help` for full command list

### Important Files
- `Design/Overview.md` - Complete project specifications (Japanese)
- `Design/cost-input-and-result.png` - UI mockup
- `Design/implementation-todo.md` - ryuzee methodology PBI plan

### User & Admin Documentation
- `docs/USER_GUIDE.md` - Complete user guide for end users
- `docs/ADMIN_GUIDE.md` - System administration and deployment guide

### Reference Documentation
Comprehensive reference docs in `/ref/` directory:

**Core Documentation:**
- `ref/README.md` - Reference documentation index and navigation
- `ref/project-overview.md` - Project architecture, goals, and current status
- `ref/architecture-overview.md` - Detailed system architecture and design patterns
- `ref/technical-specifications.md` - Cost calculation formulas, pricing data, and algorithms
- `ref/pricing-data-reference.md` - Comprehensive pricing data for all cloud providers

**Implementation & Development:**
- `ref/feature-implementation-status.md` - Complete PBI status (100% implemented)
- `ref/implementation-guide.md` - Development methodology and TDD approach
- `ref/implementation-architecture-reference.md` - Detailed system architecture and design patterns
- `ref/cost-calculation-algorithms-reference.md` - Comprehensive pricing formulas and break-even analysis
- `ref/implementation-details.md` - Comprehensive technical implementation details
- `ref/api-endpoints-reference.md` - Complete REST API documentation with examples
- `ref/development-guide.md` - Setup instructions, TDD workflow, and daily commands

**Security & Operations:**
- `ref/security-architecture.md` - Enterprise-grade security implementation details
- `ref/monitoring-observability.md` - Comprehensive monitoring and observability setup

**Testing & Quality:**
- `ref/testing-framework-guide.md` - Outside-In TDD, BDD approach, and comprehensive testing
- `ref/testing-strategy.md` - Coverage requirements and test execution strategies

**UI and Frontend:**
- `ref/ui-requirements.md` - Interface specifications, UX requirements, and design system
- `ref/frontend-architecture.md` - JavaScript, CSS, and template structure

**Deployment & Operations:**
- `ref/deployment-production-guide.md` - Production deployment strategies and operations

**Quick Start:** New developers should begin with `ref/project-overview.md` and `ref/development-guide.md`

### Key Implementation Areas
- Cost calculation engine for Lambda and VMs
- Web interface with input forms and graph visualization
- CSV export functionality
- Currency conversion handling

## Design Constraints

- 機械学習をつかった推奨機能は実装しない
- 地図をつかったリージョン比較はしない
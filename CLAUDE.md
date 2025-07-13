# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Cost comparison simulator for AWS Lambda vs Virtual Machine deployments to identify break-even points.

## Current Status

✅ **FULLY IMPLEMENTED** - Complete working application with comprehensive testing and documentation.

- ✅ Flask backend with REST API (96%+ test coverage)
- ✅ Interactive web interface with Chart.js visualization
- ✅ AWS Lambda and VM cost calculation engines
- ✅ CSV export and currency conversion features
- ✅ Production-ready code quality (linting, type checking, CI/CD)

See `Design/Overview.md` for original specifications and `/ref/` directory for implementation details.

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

### Reference Documentation
Comprehensive reference docs in `/ref/` directory:

**Core Documentation:**
- `ref/README.md` - Reference documentation index and navigation
- `ref/project-overview.md` - Project architecture, goals, and current status
- `ref/technical-specifications.md` - Cost calculation formulas, pricing data, and algorithms
- `ref/implementation-guide.md` - Development roadmap, PBI structure, and TDD methodology
- `ref/api-reference.md` - Complete REST API documentation with examples

**UI and Development:**
- `ref/ui-requirements.md` - Interface specifications, UX requirements, and design system
- `ref/frontend-architecture.md` - JavaScript, CSS, and template structure
- `ref/development-guide.md` - Setup instructions, TDD workflow, and daily commands
- `ref/testing-strategy.md` - Comprehensive testing approach and coverage requirements

**Quick Start:** New developers should begin with `ref/project-overview.md` and `ref/development-guide.md`

### Key Implementation Areas
- Cost calculation engine for Lambda and VMs
- Web interface with input forms and graph visualization
- CSV export functionality
- Currency conversion handling
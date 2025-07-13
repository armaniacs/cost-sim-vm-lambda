# Reference Documentation Index

This directory contains comprehensive reference documentation for the AWS Lambda vs VM Cost Simulator project.

## Quick Navigation

### 📋 Project Overview
- **[Project Overview](project-overview.md)** - High-level architecture, goals, and current status
- **[Technical Specifications](technical-specifications.md)** - Cost calculation formulas, pricing data, and algorithms

### 🚀 Implementation Guides
- **[Implementation Guide](implementation-guide.md)** - Development roadmap, PBI structure, and TDD methodology
- **[API Reference](api-reference.md)** - Complete REST API documentation with examples

### 🎨 UI and Frontend
- **[UI Requirements](ui-requirements.md)** - Interface specifications, UX requirements, and design system
- **[Frontend Architecture](frontend-architecture.md)** - JavaScript, CSS, and template structure

### ⚙️ Development
- **[Development Guide](development-guide.md)** - Setup instructions, TDD workflow, and daily commands
- **[Testing Strategy](testing-strategy.md)** - Comprehensive testing approach and coverage requirements

## Document Overview

| Document | Purpose | Audience |
|----------|---------|----------|
| Project Overview | Project goals, architecture, status | All stakeholders |
| Technical Specifications | Cost formulas, pricing data | Developers, analysts |
| Implementation Guide | Development methodology, PBI roadmap | Developers, PM |
| API Reference | Endpoint documentation | Frontend developers, integrators |
| UI Requirements | Interface design, UX patterns | Designers, frontend developers |
| Frontend Architecture | JavaScript structure, Chart.js | Frontend developers |
| Development Guide | Environment setup, workflows | Developers |
| Testing Strategy | Test approach, coverage goals | QA, developers |

## Key Features Documented

### Cost Calculation Engine
- AWS Lambda pricing with free tier handling
- VM cost calculations (EC2 and Sakura Cloud)
- Break-even point algorithms
- Currency conversion logic

### Interactive Visualization
- Chart.js implementation with custom plugins
- Yellow reference lines for execution frequencies
- Purple break-even point indicators
- Responsive design patterns

### Data Export
- CSV generation with Japanese localization
- UTF-8 BOM for Excel compatibility
- Comprehensive metadata inclusion

### Development Methodology
- Test-driven development (t_wada style)
- Agile implementation with PBIs
- Quality gates and code standards

## Getting Started

1. **New Developers**: Start with [Project Overview](project-overview.md) and [Development Guide](development-guide.md)
2. **Frontend Work**: Review [UI Requirements](ui-requirements.md) and [Frontend Architecture](frontend-architecture.md)
3. **API Integration**: Check [API Reference](api-reference.md)
4. **Understanding Costs**: Read [Technical Specifications](technical-specifications.md)

## Document Maintenance

These documents are maintained alongside code changes. When making significant updates:

1. Update the relevant reference document
2. Verify links and examples are current
3. Update version information if applicable
4. Consider impact on other documents

---

**Last Updated**: January 2025  
**Project Status**: ✅ Fully Implemented  
**Test Coverage**: 96%+ with 36 passing tests
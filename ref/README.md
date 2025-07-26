# Reference Documentation Index

This directory contains comprehensive reference documentation for the AWS Lambda vs VM Cost Simulator project.

## Quick Navigation

### 📋 Project Overview & Architecture
- **[Project Overview](project-overview.md)** - High-level architecture, goals, and current status
- **[Architecture Overview](architecture-overview.md)** - Detailed system architecture and design patterns
- **[Technical Specifications](technical-specifications.md)** - Cost calculation formulas, pricing data, and algorithms
- **[Pricing Data Reference](pricing-data-reference.md)** - Comprehensive pricing data for all cloud providers

### 🚀 Implementation & Development
- **[Feature Implementation Status](feature-implementation-status.md)** - Complete PBI status and roadmap
- **[Implementation Guide](implementation-guide.md)** - Development roadmap, PBI structure, and TDD methodology
- **[Implementation Architecture Reference](implementation-architecture-reference.md)** - Detailed system architecture and design patterns
- **[Cost Calculation Algorithms Reference](cost-calculation-algorithms-reference.md)** - Comprehensive pricing formulas and break-even analysis
- **[API Endpoints Reference](api-endpoints-reference.md)** - Complete REST API documentation with examples
- **[Development Guide](development-guide.md)** - Setup instructions, TDD workflow, and daily commands

### 🧪 Testing & Quality
- **[Testing Framework Guide](testing-framework-guide.md)** - Comprehensive testing approach with Outside-In TDD
- **[Testing Strategy](testing-strategy.md)** - Coverage requirements and test execution strategies

### 🔒 Security & Operations
- **[Security Architecture](security-architecture.md)** - Enterprise-grade security implementation details
- **[Monitoring & Observability](monitoring-observability.md)** - Comprehensive monitoring and observability setup

### 🎨 UI and Frontend
- **[UI Requirements](ui-requirements.md)** - Interface specifications, UX requirements, and design system
- **[Frontend Architecture](frontend-architecture.md)** - JavaScript, CSS, and template structure

### 🚀 Deployment & Operations
- **[Deployment & Production Guide](deployment-production-guide.md)** - Production deployment strategies and operations

## Document Overview

| Document | Purpose | Audience |
|----------|---------|----------|
| Project Overview | Project goals, architecture, status | All stakeholders |
| Architecture Overview | System design, patterns, data flow | Architects, senior developers |
| Technical Specifications | Cost formulas, pricing data | Developers, analysts |
| Pricing Data Reference | Complete pricing information, sources | Developers, business analysts |
| Feature Implementation Status | PBI completion status, roadmap | Project managers, stakeholders |
| Implementation Guide | Development methodology, PBI roadmap | Developers, PM |
| API Endpoints Reference | Complete REST API documentation | Frontend developers, integrators |
| Development Guide | Environment setup, workflows | Developers |
| Testing Framework Guide | Outside-In TDD, BDD approach | QA, developers |
| Testing Strategy | Test approach, coverage goals | QA, developers |
| UI Requirements | Interface design, UX patterns | Designers, frontend developers |
| Frontend Architecture | JavaScript structure, Chart.js | Frontend developers |
| Deployment & Production Guide | Production deployment, operations | DevOps, system administrators |

## Key Features Documented

### Multi-Cloud Cost Calculation Engine
- AWS Lambda pricing with free tier handling
- VM cost calculations (6 providers: AWS EC2, Google Cloud, Azure, OCI, Sakura Cloud)
- Internet egress cost calculations with transfer ratio settings
- Break-even point algorithms with comprehensive provider comparison
- Currency conversion logic (USD/JPY)

### Interactive Visualization
- Chart.js implementation with custom plugins
- Real-time cost comparison graphs
- Break-even point indicators
- Responsive design patterns
- Interactive data point exploration

### Advanced Features
- Internet transfer ratio configuration (0-100%)
- Always Free tier support (OCI, Azure B1ls)
- CSV generation with comprehensive export data
- Multi-provider break-even analysis
- Lambda equivalent VM recommendations

### Production-Ready Implementation
- Docker containerization with multi-stage builds
- Comprehensive test suite (133 tests, 88% coverage)
- Outside-In TDD with BDD scenarios
- Production deployment configurations
- Security hardening and performance optimization

### Development Methodology
- Test-driven development (Outside-In TDD + t_wada style)
- ryuzee methodology with PBI management
- Quality gates and code standards
- Comprehensive CI/CD pipeline

## Getting Started

1. **New Developers**: Start with [Project Overview](project-overview.md) and [Development Guide](development-guide.md)
2. **Architecture Understanding**: Review [Architecture Overview](architecture-overview.md)
3. **Frontend Work**: Check [UI Requirements](ui-requirements.md) and [Frontend Architecture](frontend-architecture.md)
4. **API Integration**: Reference [API Endpoints Reference](api-endpoints-reference.md)
5. **Understanding Costs**: Read [Technical Specifications](technical-specifications.md) and [Pricing Data Reference](pricing-data-reference.md)
6. **Testing Approach**: Study [Testing Framework Guide](testing-framework-guide.md)
7. **Production Deployment**: Follow [Deployment & Production Guide](deployment-production-guide.md)

## Document Maintenance

These documents are maintained alongside code changes. When making significant updates:

1. Update the relevant reference document
2. Verify links and examples are current
3. Update version information if applicable
4. Consider impact on other documents

---

**Last Updated**: January 2025  
**Project Status**: ✅ 100% Complete - Production Ready  
**Total PBIs**: 10 (39 story points)  
**Test Coverage**: 88% with 133 passing tests  
**Supported Providers**: 6 cloud providers (AWS, Google Cloud, Azure, OCI, Sakura Cloud)  
**Key Features**: Multi-cloud cost comparison, egress calculations, break-even analysis
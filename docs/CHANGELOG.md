# Changelog

All notable changes to Recruiter-Pro-AI will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).

## [2.0.0] - 2026-01-29

### Added
- **4-Agent Hybrid Architecture**
  - Agent 1: File Parser (PDF/DOCX/TXT support)
  - Agent 2: Data Extractor (regex-based, deterministic)
  - Agent 3: Hybrid Scorer (rule-based 60% + ML 40%)
  - Agent 4: LLM Explainer (Ollama integration)

- **Storage Layer**
  - SQLite database for match history
  - Pydantic models for type safety
  - Database migration tools

- **Configuration System**
  - YAML-based configuration
  - Environment variable support
  - Multi-environment setup (dev/prod)

- **Testing Infrastructure**
  - 14 unit tests (storage layer)
  - 12 integration tests (agents + pipeline)
  - pytest configuration

### Changed
- Migrated from 3-agent to 4-agent architecture
- Replaced hardcoded configs with YAML files
- Improved error handling and logging

### Fixed
- Import inconsistencies across modules
- Data type mismatches in agent outputs
- Missing skill matching logic

### Removed
- Deprecated backup files
- Duplicate datasets
- Old test files

## [1.0.0] - Previous Version

Initial implementation with basic 3-agent system.

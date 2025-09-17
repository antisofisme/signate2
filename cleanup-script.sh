#!/bin/bash

# Documentation Cleanup Script
# Consolidate scattered documentation into organized structure

echo "🧹 Starting documentation cleanup..."

# Create final structure
mkdir -p docs/final/{implementation,architecture,workflows,guides}
mkdir -p docs/archive/{old-docs,deprecated,duplicates}

# Archive old/duplicate files
echo "📁 Archiving outdated documents..."

# Move old architecture docs that are superseded
mv docs/ARCHITECTURAL_DECISIONS.md docs/archive/old-docs/ 2>/dev/null
mv docs/BACKEND_ARCHITECTURE.md docs/archive/old-docs/ 2>/dev/null
mv docs/FRONTEND_ARCHITECTURE.md docs/archive/old-docs/ 2>/dev/null
mv docs/PROJECT_ARCHITECTURE.md docs/archive/old-docs/ 2>/dev/null
mv docs/WORKER_DEPLOYMENT_ARCHITECTURE.md docs/archive/old-docs/ 2>/dev/null
mv docs/executive-summary.md docs/archive/old-docs/ 2>/dev/null
mv docs/PROJECT_STRUCTURE_SUMMARY.md docs/archive/old-docs/ 2>/dev/null

# Move redundant implementation docs
mv docs/refinement-implementation-plan.md docs/archive/deprecated/ 2>/dev/null
mv docs/development-workflow.md docs/archive/duplicates/ 2>/dev/null
mv docs/system-architecture.md docs/archive/duplicates/ 2>/dev/null

# Move deployment docs to archive (will be consolidated)
mv docs/deployment/ docs/archive/old-docs/ 2>/dev/null

# Keep final relevant documents
echo "✅ Keeping relevant documents..."
# These will stay in docs/ and be reorganized:
# - COMPREHENSIVE_DEVELOPMENT_SUMMARY.md (executive summary)
# - CLARIFICATION_QUESTIONS.md (stakeholder Q&A)
# - backend-compatibility-validation-report.md (technical analysis)
# - claude-code-concurrent-execution-guide.md (AI workflow)
# - technical-specifications.md (specs)
# - testing-strategy.md (QA approach)

echo "📋 Documents cleanup completed!"
echo "Check docs/final/ for organized structure"
echo "Check docs/archive/ for moved files"
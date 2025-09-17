#!/bin/bash

echo "🧹 COMPREHENSIVE PROJECT CLEANUP"
echo "Consolidating scattered folders and files..."

# Create organized structure
mkdir -p project-archive/
mkdir -p docs/archive/old-folders/

# Move scattered folders to archive
echo "📁 Archiving scattered folders..."
mv specification/ docs/archive/old-folders/ 2>/dev/null
mv research/ docs/archive/old-folders/ 2>/dev/null  
mv planning/ docs/archive/old-folders/ 2>/dev/null
mv architecture/ docs/archive/old-folders/ 2>/dev/null
mv design/ docs/archive/old-folders/ 2>/dev/null
mv config/ docs/archive/old-folders/ 2>/dev/null
mv coordination/ docs/archive/old-folders/ 2>/dev/null
mv project-plan/ docs/archive/old-folders/ 2>/dev/null

# Keep essential folders
echo "✅ Keeping essential folders:"
echo "  - project/ (backend + frontend)"
echo "  - docs/ (consolidated documentation)"  
echo "  - docker/ (deployment configs)"
echo "  - memory/ (claude-flow data)"

# Remove empty or unnecessary folders
echo "🗑️ Removing empty folders..."
rmdir */ 2>/dev/null || true

echo "✅ Cleanup completed!"
echo "📁 Archived folders moved to: docs/archive/old-folders/"
echo "📋 Current structure:"
ls -la | grep "^d"

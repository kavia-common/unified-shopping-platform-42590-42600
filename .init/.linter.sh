#!/bin/bash
cd /home/kavia/workspace/code-generation/unified-shopping-platform-42590-42600/backend
source venv/bin/activate
flake8 .
LINT_EXIT_CODE=$?
if [ $LINT_EXIT_CODE -ne 0 ]; then
  exit 1
fi


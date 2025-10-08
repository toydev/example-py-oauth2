#!/bin/bash
echo "PWD: $PWD" >&2
echo "PATH: $PATH" >&2
cd /mnt/d/Workspace/Sandbox/auth/mcp-oauth-hello
exec npm run mcp

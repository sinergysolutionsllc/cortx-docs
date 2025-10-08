# 🚀 Quick Start Guide

## One-Command Startup

### Option 1: Using npm scripts (Recommended)

```bash
cd /Users/michael/Development/sinergysolutionsllc
npm install  # Install concurrently
npm run dev  # Start all services
```

### Option 2: Using shell script

```bash
cd /Users/michael/Development/sinergysolutionsllc
./start-all.sh
```

## Access the UIs

Once started, open these URLs in your browser:

| Service | URL | Main Feature |
|---------|-----|--------------|
| **CORTX Designer** | <http://localhost:3000/designer> | Visual BPM workflow designer with AI assistant |
| **OffermAit** | <http://localhost:3001> | Investment management |
| **CORTX Suites** | <http://localhost:3002> | Suite management |
| **FedSuite** | <http://localhost:3003> | Federal compliance |

## CORTX Designer Features (Port 3000)

### Main Routes

- `/` - Home page
- `/designer` - **Visual workflow designer** (main feature)
- `/processes` - Process list

### Designer Features

1. **Node Palette** (Left) - Drag and drop workflow nodes
2. **Canvas** (Center) - Visual workflow builder
3. **Toolbar** - Controls:
   - Undo/Redo
   - Zoom controls
   - Auto-layout
   - Export (PNG, SVG, JSON)
   - **Compile** - Compile to rulepack
   - **Save** - Save process
4. **Properties Panel** (Right) - Edit selected node
5. **AI Assistant** - Natural language workflow generation

### How to Use Designer

1. Click **"Show AI Assistant"** button (top right)
2. Type what you want to build: *"Create a GTAS monthly submission workflow"*
3. Or drag nodes from palette to canvas
4. Click nodes to edit properties in right panel
5. Connect nodes by dragging from output to input
6. Click **Compile** to generate rulepack
7. Click **Save** to persist workflow

## Individual Service Commands

### Start One Service

```bash
# CORTX Designer
cd /Users/michael/Development/sinergysolutionsllc/cortx-designer/frontend
npm run dev  # Port 3000

# OffermAit
cd /Users/michael/Development/OffermAit/frontend
npm run dev -- -p 3001

# CORTX Suites
cd /Users/michael/Development/cortx-suites/frontend
npm run dev -- -p 3002

# FedSuite
cd /Users/michael/Development/sinergysolutionsllc/fedsuite/frontend
npm run dev -- -p 3003
```

### Build Services

```bash
cd /Users/michael/Development/sinergysolutionsllc
npm run build:all  # Build all
npm run build:designer  # Build designer only
```

## Stop All Services

Press `Ctrl+C` in the terminal running the services.

## Troubleshooting

### Port Already in Use

```bash
# Find process using port
lsof -i :3000

# Kill it
kill -9 <PID>
```

### Services Won't Start

```bash
# Install dependencies
cd /Users/michael/Development/sinergysolutionsllc
npm run install:all
```

### Clear Cache

```bash
cd <service-directory>
rm -rf .next node_modules package-lock.json
npm install
```

## Backend Services (Optional)

If you need backend APIs:

```bash
# Workflow Service (for compilation)
cd /Users/michael/Development/sinergysolutionsllc/services/workflow
python -m uvicorn app.main:app --reload --port 8004

# Gateway (API Gateway)
cd /Users/michael/Development/sinergysolutionsllc/services/gateway
python -m uvicorn app.main:app --reload --port 8000
```

## Next Steps

1. **Explore CORTX Designer**: <http://localhost:3000/designer>
2. **Try AI Assistant**: Click "Show AI Assistant" and describe a workflow
3. **Build a Workflow**: Drag nodes, connect them, compile
4. **Navigate Between UIs**: Use the browser tabs for different services

For detailed documentation, see `START_ALL_SERVICES.md`

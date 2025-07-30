# AI Trading Sentinel Frontend

## Overview

This is the frontend for the AI Trading Sentinel system. It provides a user interface for monitoring and controlling trading activities, viewing signals, and managing broker connections.

## Features

- Dashboard with signal cards and status panels
- Compounding tracker
- Broker admin panel
- Remote control panel
- Mutation Sentinel Banner

## Getting Started

### Prerequisites

- Node.js (v14 or higher)
- npm or yarn

### Installation

```bash
# Install dependencies
npm install
```

### Environment Setup

Create a `.env` file in the frontend directory with the following variables:

```
VITE_API_URL=http://localhost:5000
```

You can copy the `.env.example` file as a starting point.

### Development

```bash
# Start development server
npm run dev
```

The development server will be available at http://localhost:5173/

### Building for Production

```bash
# Build for production
npm run build
```

## Banner Integration

The Mutation Sentinel Banner has been integrated into the frontend as a React component. For detailed information about the banner integration, see:

- `BANNER_INTEGRATION.md` - Details about the React component
- `../BANNER_INTEGRATION_GUIDE.md` - Comprehensive guide for all integration options
- `../ui/README.md` - Information about the standalone UI components

### Testing the Banner

To test the banner integration:

```bash
# Run tests for the banner component
npm test -- -t "SentinelBanner"
```

Or use the provided test scripts:

```bash
# Windows
..\test_banner_integration.bat

# Unix/Linux/macOS
../test_banner_integration.sh
```

## Troubleshooting

### API Connection Errors

When running the frontend without the backend, you'll see API connection errors in the console. These are expected and don't affect the banner functionality.

### Environment Variable Errors

If you see a `process is not defined` error, make sure to use `import.meta.env.VITE_*` instead of `process.env.REACT_APP_*` since the project uses Vite.

## Project Structure

- `src/` - Source code
  - `components/` - React components
    - `SentinelBanner.tsx` - The Mutation Sentinel Banner component
    - `SentinelBanner.css` - Styles for the banner
    - `SentinelBanner.test.tsx` - Tests for the banner
  - `App.tsx` - Main application component
  - `main.tsx` - Entry point
- `public/` - Static assets
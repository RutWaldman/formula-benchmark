# Frontend Deployment Guide

This guide explains how to deploy the Dynamic Formula Benchmark Dashboard to Vercel.

## Prerequisites

- A [Vercel account](https://vercel.com)
- The backend API deployed and accessible (optional - see API Configuration below)
- Git repository connected to Vercel

## Environment Variables

### VITE_API_BASE_URL

The frontend uses `VITE_API_BASE_URL` environment variable to connect to the backend API.

**Configuration options:**

1. **Same-domain API (using Vercel rewrites)**
   - Leave `VITE_API_BASE_URL` empty or set to `/api`
   - Update `vercel.json` rewrites to point to your actual API URL
   - Requests to `/api/*` will be proxied to your backend

2. **Cross-origin API**
   - Set `VITE_API_BASE_URL` to your full API URL (e.g., `https://api.yourdomain.com`)
   - Ensure your backend has proper CORS configuration

## Deployment Steps

### Option 1: Deploy via Vercel CLI

```bash
# Install Vercel CLI
npm install -g vercel

# Navigate to frontend directory
cd frontend

# Deploy to Vercel
vercel

# For production deployment
vercel --prod
```

### Option 2: Deploy via Vercel Dashboard

1. Go to [Vercel Dashboard](https://vercel.com/dashboard)
2. Click "Add New" → "Project"
3. Import your Git repository
4. Set the following:
   - **Framework Preset**: Vite
   - **Root Directory**: `frontend`
   - **Build Command**: `npm run build`
   - **Output Directory**: `dist`
5. Add environment variables:
   - `VITE_API_BASE_URL`: Your API URL
6. Click "Deploy"

## Vercel Configuration

The `vercel.json` file includes:

- **Build settings**: Vite framework with proper build/output directories
- **Rewrites**: API proxy configuration (update the destination URL)
- **Headers**: Security headers (X-Content-Type-Options, X-Frame-Options, X-XSS-Protection)

### Updating API Rewrites

Edit `vercel.json` and update the rewrites destination:

```json
{
  "rewrites": [
    {
      "source": "/api/:path*",
      "destination": "https://YOUR-ACTUAL-API-URL.com/api/:path*"
    }
  ]
}
```

## Local Development

For local development:

1. Copy `.env.example` to `.env`:
   ```bash
   cp .env.example .env
   ```

2. Update `.env` with your local API URL (default: `http://localhost:8000`)

3. Start the development server:
   ```bash
   npm run dev
   ```

## Build Verification

Before deploying, verify the build works locally:

```bash
npm run build
npm run preview
```

## Troubleshooting

### API Connection Issues

1. Check that `VITE_API_BASE_URL` is correctly set
2. Verify CORS is configured on your backend
3. Check browser console for network errors

### Build Failures

1. Ensure all dependencies are installed: `npm install`
2. Check for TypeScript errors: `npx tsc --noEmit`
3. Review Vercel build logs for specific errors

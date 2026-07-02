# Vercel Deployment Guide & Troubleshooting

## The Issue: Why wasn't data loading on Vercel?
Locally, your Next.js application used a rewrite rule in `next.config.ts` to proxy requests from `/api/*` to your local FastAPI server at `http://127.0.0.1:8000`. 
When you deployed to Vercel using their `experimentalServices` monorepo feature, Vercel deployed your Python backend to a special internal path: `/_/backend`. 
Because your frontend code was still trying to fetch from `/api/hitters` (which was trying to route to localhost), it couldn't find the backend.

## The Fix
We made two main changes to fix this:

1. **Configured `vercel.json`**: We told Vercel exactly how to build and route your Python backend by setting `"framework": "fastapi"`.
2. **Updated API Base URL**: In `frontend/lib/api.ts`, we updated the base URL to dynamically check the environment:
   ```typescript
   const BASE = process.env.NODE_ENV === "production" ? "/_/backend/api/hitters" : "/api/hitters";
   ```
3. **Moved Data Files**: Vercel's `experimentalServices` isolates each service. This meant your Python backend couldn't read the `.csv` files stored in the project root. We moved all `.csv` files into the `backend/` directory and updated `backend/services/data_service.py` so they are now successfully packaged and deployed with the Vercel serverless function!

---

## Step-by-Step Deployment Instructions

Follow these instructions to push the fix and deploy your updated app on Vercel:

### 1. Commit and Push the Fixes to GitHub
Open your terminal in the project root directory and run the following commands to send our fixes to your repository:
```bash
git add vercel.json frontend/lib/api.ts
git commit -m "fix: resolve vercel deployment and backend routing issues"
git push origin main
```

### 2. Monitor the Vercel Deployment
1. Go to your [Vercel Dashboard](https://vercel.com/dashboard).
2. Click on your project (`Hitters-Hub`).
3. You should see a new deployment building automatically since you pushed to the `main` branch.
4. Click on the building deployment to view the logs. You should see both `frontend` and `backend` building successfully.

### 3. Verify the Fix
Once the deployment status turns to **Ready** (Green):
1. Click the **Visit** button or the provided domains in Vercel.
2. Your application should now load the UI *and* successfully fetch the predictions data from the backend!

### Note on Future Local Development
These changes will not break your local development! When you run `npm run dev` locally, `process.env.NODE_ENV` is set to `"development"`, so the application will continue to use your local proxy to `127.0.0.1:8000` just like before.

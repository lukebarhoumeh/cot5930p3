# COT 5930 – Project 3

**Name**: Ibrahim “Luke” Barhoumeh (Z23652726)  
**Date**: March 2025  
**Professor**: Andrade  

---

## 1. Overview

In this project, I extended my previous work from Projects 1 and 2 by integrating **change management** and **automated deployment** in a **blue/green** context using Google Cloud. The objectives included:

- **Automated CI/CD** from GitHub to Cloud Run via **Cloud Build** triggers.  
- **Two parallel versions** of the Flask application—one “blue” and one “green”—with traffic split 50/50 at the Cloud Run layer, **without** any custom logic in my code.  
- Retaining a private Google Cloud Storage (GCS) bucket and the Gemini AI API for image captioning.

### Key Advancements from Project 2

- **Automation**: I introduced Cloud Build triggers so that all pushes to GitHub automatically build and deploy the container—no manual `gcloud` commands needed.  
- **Blue/Green Strategy**: Two distinct Cloud Build configurations (`cloudbuild_blue.yaml` and `cloudbuild_green.yaml`) deploy separate revisions with different environment variables (`BG_COLOR=blue` / `BG_COLOR=green`).  
- **Parallel Revisions**: Cloud Run runs both “blue” and “green” versions concurrently, each receiving 50% of incoming requests.

---

## 2. Architecture & Flow

1. **User Upload**  
   - A user visits `https://<Cloud Run URL>` and uploads a JPEG.  
   - Flask saves the file locally and calls **Gemini AI** to generate a concise caption.

2. **AI Captioning** (Gemini / Generative Language API)  
   - The application sends the image in base64 format with a prompt asking for JSON output containing a `"title"` and `"description"`.  
   - The returned caption is then stored alongside the image.

3. **Storage in GCS**  
   - Both the image (`filename.jpg`) and corresponding JSON (`filename.json`) are uploaded to a **private** GCS bucket.  
   - Users never receive direct GCS URLs; the Flask app mediates access.

4. **Blue/Green Deployment**  
   - Two **Cloud Build** YAML files:
     - `cloudbuild_blue.yaml` → sets `BG_COLOR=blue`  
     - `cloudbuild_green.yaml` → sets `BG_COLOR=green`  
   - Each build config deploys to the same Cloud Run service but creates distinct revisions.  
   - Cloud Run **Manage Traffic** splits requests evenly (50/50) between the two revisions.

5. **No Hardcoded Secrets**  
   - The `GENAI_API_KEY` is passed as an environment variable.  
   - `BG_COLOR` is likewise set at deploy time, ensuring no code-based color splitting logic.

---

## 3. Deployment Pipeline (Automated CI/CD)

1. **GitHub Repository**  
   - I maintain all source files (`main.py`, `Dockerfile`, `cloudbuild_blue.yaml`, `cloudbuild_green.yaml`, etc.) in a single repository, without committing secrets or service account JSON files.

2. **Cloud Build Triggers**  
   - **Trigger 1**: Deploys “blue” (`cloudbuild_blue.yaml`).  
   - **Trigger 2**: Deploys “green” (`cloudbuild_green.yaml`).  
   - Each commit (or manual trigger run) packages and deploys a new revision automatically.

3. **Build & Deploy Steps**  
   - Install dependencies and run placeholder tests (`echo "No tests yet"`).  
   - **Build & push** Docker image to Container Registry.  
   - **Deploy** to Cloud Run, specifying `BG_COLOR=blue` or `BG_COLOR=green`.

4. **Traffic Split**  
   - After both revisions are deployed, I configure a **50/50** traffic split in **Cloud Run** → “Manage Traffic.”  
   - Half the users see a **blue** background, half see **green**, with no custom code logic needed.

---

## 4. Application URL & Usage

- **Cloud Run URL**: `[INSERT YOUR PUBLIC URL HERE]`

**Usage**:
1. Navigate to the URL, landing on a **blue** or **green** background (depending on the assigned revision).  
2. Upload a JPEG; the application calls Gemini AI for a short description.  
3. Both the image and JSON metadata are stored in GCS.  
4. The home page lists available images from GCS; clicking a file displays the image and AI-generated description.

---

## 5. Pros & Cons

### Pros
- **Automated & Scalable**: Zero manual CLI deploy steps; Cloud Run scales seamlessly based on demand.  
- **Safe Deployments**: Blue/green approach allows me to run new code in parallel with the old. If something fails, it’s straightforward to roll back or reduce traffic to the problematic revision.  
- **Secure**: My GCS bucket is private, no service account JSON is exposed, and environment variables handle secrets.  
- **Simple Code Structure**: Flask endpoints are clearly separated from AI calls and GCS operations.

### Cons
- **Placeholder Tests**: I only have a stub test step. In a real system, I would develop more robust testing.  
- **Potential Latency**: AI calls could add noticeable delays for large images.  
- **Cost**: AI inference, data storage, and egress costs may rise significantly for high traffic.  
- **Single Region**: Currently not multi-region. For global use, I would explore multi-region Cloud Run and GCS replication.

---

## 7. Links & Access

- **Cloud Run Service URL**: `[https://imaging-app-856239458079.us-east1.run.app]`  
- **GCP Console**: `[https://console.cloud.google.com/home/dashboard?project=ibarhoumeh-cot5930p1]` 



---

## 8. Conclusion

In this Project 3, I introduced an **automated build** pipeline, a **blue/green deployment** approach, and a 50/50 **traffic split** in Cloud Run—without coding any custom traffic logic in the application. This meets the requirements of a production-ready, serverless environment that scales and can be safely iterated upon for future enhancements.

**End of README**

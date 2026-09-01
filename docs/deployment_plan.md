# Deployment Plan

Goal: deploy the AgPV Assistant so Purdue users can access it through a browser
without making the app publicly open.

## Privacy Model

There are three separate privacy/security layers:

```text
private GitHub/GHCR or RCAC registry -> protects the container image/code
Geddes private Ingress -> keeps the app Purdue-network/VPN only
Geddes secrets -> keeps API keys and license values out of code
```

Do not put API keys, MATLAB license values, or `.env` files inside the Docker
image or GitHub repository.

## Phase 1: Local Docker Test

1. Add deployment files in the project root:

```text
D:\agpv-ai-consultant\Dockerfile
D:\agpv-ai-consultant\.dockerignore
```

2. Build the Docker image locally:

```powershell
cd D:\agpv-ai-consultant
docker build --platform linux/amd64 -t agpv-assistant .
```

3. Run the container locally:

```powershell
docker run --rm -p 8501:8501 -e PURDUE_GENAI_KEY=your_key_here agpv-assistant
```

4. Open the app:

```text
http://localhost:8501
```

This confirms the app can run inside a container before trying Geddes.

## Phase 2: Store Image Privately

Push the working image to one private registry:

```text
Option A: GitHub Container Registry (ghcr.io)
Option B: RCAC private registry
```

If using a private registry, Geddes needs credentials to pull the image. These
credentials should be stored in Rancher/Geddes as a registry secret.

## Phase 3: Deploy On Geddes

1. Confirm CEED has Geddes/Rancher access.
2. Create a Rancher workload/deployment.
3. Set the container image to the private image from GHCR or RCAC registry.
4. Set the app/container port:

```text
8501
```

5. Add environment variables through Geddes secrets:

```text
PURDUE_GENAI_KEY
MLM_LICENSE_FILE   # only if MATLAB is inside the container
```

6. Create a service pointing to the Streamlit container port.
7. Create a private Ingress for a Purdue-only URL.

Final access pattern:

```text
Purdue user/VPN -> private Geddes URL -> Streamlit app
```

## MATLAB/PVMAPS Decision

MATLAB/PVMAPS is the hardest part of deployment.

Two possible approaches:

```text
Option A: MATLAB inside the Docker container
Option B: PVMAPS runs on a separate MATLAB-enabled lab/RCAC machine
```

For Option A, the image may need to start from a MathWorks MATLAB base image:

```dockerfile
FROM mathworks/matlab:r2024b
```

The container must be configured to reach Purdue's MATLAB license server using:

```text
MLM_LICENSE_FILE=27000@<license-server>
```

The exact license-server value should come from RCAC or Purdue IT, not from the
codebase.

## Recommended Sequence

```text
1. Dockerize and test app locally
2. Deploy Streamlit + GenAI Studio + RAG on Geddes
3. Confirm private Purdue-only access works
4. Add MATLAB/PVMAPS container or separate backend
5. Later add multiple PVMAPS runs and quick ML estimator
```

## Questions For RCAC / PI

- Does CEED already have a Geddes/Rancher project?
- Should the image be hosted on private GHCR or RCAC private registry?
- Can Geddes pull private GHCR images using a GitHub token secret?
- What MATLAB release should the container use?
- What `MLM_LICENSE_FILE` value should be used for Purdue's MATLAB license?
- Can Geddes containers reach the MATLAB license server?
- Should PVMAPS files be copied into the image or mounted from shared storage?

## References

- Geddes access: https://docs.rcac.purdue.edu/userguides/geddes/access/
- Geddes concepts/Rancher: https://docs.rcac.purdue.edu/userguides/geddes/concepts/
- Geddes web server/Ingress: https://docs.rcac.purdue.edu/userguides/geddes/examples/webserver/
- Geddes registry docs: https://www.rcac.purdue.edu/knowledge/geddes?all=true
- Docker getting started: https://docs.docker.com/get-started/
- GitHub Container Registry: https://docs.github.com/en/packages/working-with-a-github-packages-registry/working-with-the-container-registry
- MATLAB Docker container: https://www.mathworks.com/help/cloudcenter/ug/matlab-container-on-docker-hub.html
- Custom MATLAB container: https://www.mathworks.com/help/cloudcenter/ug/create-a-custom-matlab-container.html


# THE ROADMAP (v3): First-Principles Deployment

**Objective:** Deploy all three commercial assets using direct, fundamental commands.

---

### Phase 1: Deploy `agent.forge` (The Text-Agent Factory)

This asset is the most mature. We use the existing Railway project and deploy to it directly.

*   **1.1: Link & Configure.**
    *   **Directory:** `cd "/Users/aijesusbro/AI Projects/agent-forge"`
    *   **Action:** Link the local directory to the existing Railway project and set secrets. This establishes the connection and injects the environment.
    *   **Commands:**
        ```bash
        railway link --project 3730672b-e880-4ec6-b534-da1479ee843a
        railway variables set JWT_SECRET=$(openssl rand -hex 32) SERVICE_TOKEN=$(openssl rand -hex 32)
        ```

*   **1.2: Deploy.**
    *   **Action:** Trigger the deployment. Railway will read your `railway.toml` and `Dockerfile` and build the service.
    *   **Command:**
        ```bash
        railway up
        ```

*   **1.3: Go Live.**
    *   **Action:** Get the public URL from Railway and point your custom domain to it.
    *   **Command:**
        ```bash
        railway domain
        ```

---

### Phase 2: Deploy the ClearVC Voice Agent (The First Voice Asset)

We treat this as a new, standalone application. We will initialize a fresh project for it on Railway.

*   **2.1: Stabilize the Brain.**
    *   **Objective:** Ensure the `clearvc-amber-brain` can run reliably as a standalone service.
    *   **Action:** From the `ClearVC/amber-brain` directory, run the application locally. Diagnose and fix the `Exited (255)` error from the Docker logs.

*   **2.2: Initialize & Deploy.**
    *   **Directory:** `cd "/Users/aijesusbro/AI Projects/ClearVC/amber-brain"`
    *   **Action:** Initialize a new Railway project from this directory. This will create a new, isolated environment for the ClearVC agent.
    *   **Command:**
        ```bash
        railway init
        ```
        *(Follow the interactive prompts to name the project, e.g., `clearvc-brain`)*

*   **2.3: Configure & Activate.**
    *   **Action:** Set the production secrets for GHL and Retell in the new Railway project's variables. Then, point the ClearVC phone number's webhook in Retell to the new live URL provided by `railway domain`.

---

### Phase 3: Deploy the Advisory 9 Voice Agent (The Replication)

We replicate the clean, successful pattern from Phase 2.

*   **3.1: Forge the New Brain.**
    *   **Objective:** Create the standalone codebase for the Advisory 9 agent.
    *   **Action:**
        1.  `cp -r /Users/aijesusbro/AI\ Projects/ClearVC/amber-brain /Users/aijesusbro/AI\ Projects/Advisory9/rebecca-brain`
        2.  Modify the new `rebecca-brain` codebase to use the `advisory9_voice_agent_prompt.md` logic.

*   **3.2: Initialize & Deploy.**
    *   **Directory:** `cd "/Users/aijesusbro/AI Projects/Advisory9/rebecca-brain"`
    *   **Action:** Initialize another new, isolated Railway project for this agent.
    *   **Command:**
        ```bash
        railway init
        ```
        *(Name this project `advisory9-brain`)*

*   **3.3: Configure & Activate.**
    *   **Action:** Set the specific production secrets for Advisory 9's GHL and a new Retell agent in its Railway project variables. Point the new phone number's webhook to the live URL.

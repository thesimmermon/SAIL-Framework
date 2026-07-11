# Deploying with a Custom Domain (getsail.org)

This site is built to be hosted on **GitHub Pages** out of the `docs/` folder.

To point `https://getsail.org` to this repository, a `CNAME` file has been added to the `docs/` folder containing the domain name.

### Step 1: Push to GitHub
Commit and push the changes in this repository (including the new `CNAME` file) to your GitHub repository.

### Step 2: Configure your DNS Provider
Log in to the DNS provider where you purchased `getsail.org` (e.g., GoDaddy, Namecheap, Cloudflare, etc.) and configure the following records to point to GitHub Pages:

#### Option A: Apex Domain (getsail.org)
Create **four A records** pointing to GitHub's IP addresses:
- **Type**: A
- **Name/Host**: `@` (or leave blank)
- **Value**: `185.199.108.153`
- **Type**: A
- **Name/Host**: `@` (or leave blank)
- **Value**: `185.199.109.153`
- **Type**: A
- **Name/Host**: `@` (or leave blank)
- **Value**: `185.199.110.153`
- **Type**: A
- **Name/Host**: `@` (or leave blank)
- **Value**: `185.199.111.153`

#### Option B: `www` Subdomain (www.getsail.org)
Create a **CNAME record** pointing to your GitHub Pages URL:
- **Type**: CNAME
- **Name/Host**: `www`
- **Value**: `thesimmermon.github.io`

### Step 3: Enforce HTTPS
Once your DNS changes have propagated (this can take anywhere from a few minutes to a few hours):
1. Go to your GitHub repository on the web.
2. Navigate to **Settings** > **Pages**.
3. Under the "Custom domain" section, you should see `getsail.org`.
4. Check the box for **"Enforce HTTPS"** to ensure all traffic is securely routed over HTTPS.

Your site will now be fully accessible at `https://getsail.org`!

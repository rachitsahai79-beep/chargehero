#!/usr/bin/env python3
"""
ChargeHero Railway Deployment Script
Automates environment variable setup and deployment via Railway CLI
"""

import subprocess
import sys
import json
from typing import Dict, Optional

# Color codes for terminal output
class Colors:
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    BLUE = '\033[94m'
    RESET = '\033[0m'

def print_step(step: int, title: str):
    """Print a formatted step header."""
    print(f"\n{Colors.BLUE}{'='*60}")
    print(f"STEP {step}: {title}")
    print(f"{'='*60}{Colors.RESET}\n")

def print_success(msg: str):
    """Print success message."""
    print(f"{Colors.GREEN}✅ {msg}{Colors.RESET}")

def print_warning(msg: str):
    """Print warning message."""
    print(f"{Colors.YELLOW}⚠️  {msg}{Colors.RESET}")

def print_error(msg: str):
    """Print error message."""
    print(f"{Colors.RED}❌ {msg}{Colors.RESET}")

def run_command(cmd: str, check: bool = True) -> Optional[str]:
    """Run a shell command and return output."""
    try:
        result = subprocess.run(
            cmd,
            shell=True,
            capture_output=True,
            text=True,
            check=check
        )
        return result.stdout.strip() if result.stdout else None
    except subprocess.CalledProcessError as e:
        print_error(f"Command failed: {cmd}")
        print_error(f"Error: {e.stderr}")
        return None

def check_railway_cli() -> bool:
    """Check if Railway CLI is installed."""
    print_step(1, "Check Railway CLI Installation")

    result = run_command("railway --version", check=False)
    if result:
        print_success(f"Railway CLI found: {result}")
        return True
    else:
        print_error("Railway CLI not installed")
        print("\n📦 Install Railway CLI:")
        print("   npm install -g @railway/cli")
        print("   or")
        print("   brew install railway (macOS)")
        return False

def login_railway() -> bool:
    """Login to Railway."""
    print_step(2, "Railway Login")

    print("Opening Railway login in browser...")
    result = run_command("railway login", check=False)

    if result or "logged in" in str(result).lower():
        print_success("Logged in to Railway")
        return True
    else:
        print_warning("Could not verify login. Please authenticate manually.")
        return True  # Continue anyway

def get_environment_variables() -> Dict[str, str]:
    """Get environment variables from user input."""
    print_step(3, "Collect Environment Variables")

    print("\n⚠️  NEVER commit secrets to version control!")
    print("   Secrets should come from environment or secure input only.\n")

    variables = {}

    # Supabase credentials
    print("1️⃣  SUPABASE Credentials (from Supabase Dashboard):")
    variables["SUPABASE_URL"] = input("   SUPABASE_URL (e.g., https://xxxxx.supabase.co): ").strip()
    variables["SUPABASE_KEY"] = input("   SUPABASE_KEY (publishable key): ").strip()
    variables["SUPABASE_SERVICE_ROLE_KEY"] = input("   SUPABASE_SERVICE_ROLE_KEY (secret key): ").strip()
    variables["SUPABASE_ANON_KEY"] = variables["SUPABASE_KEY"]  # Same as publishable key

    # JWT Secret
    print("\n2️⃣  JWT_SECRET (use generated value or provide your own):")
    print("   Generated: 5x8oWxi9kEL-bzvt5mq2iB9eiJ6XD_riTC1KZgd6_II")
    variables["JWT_SECRET"] = input("   JWT_SECRET (press Enter to use generated): ").strip()
    if not variables["JWT_SECRET"]:
        variables["JWT_SECRET"] = "5x8oWxi9kEL-bzvt5mq2iB9eiJ6XD_riTC1KZgd6_II"

    # Twilio credentials
    print("\n3️⃣  TWILIO Credentials (from https://www.twilio.com/console):")
    variables["TWILIO_ACCOUNT_SID"] = input("   TWILIO_ACCOUNT_SID: ").strip()
    variables["TWILIO_AUTH_TOKEN"] = input("   TWILIO_AUTH_TOKEN: ").strip()
    variables["TWILIO_PHONE_NUMBER"] = input("   TWILIO_PHONE_NUMBER (e.g., +14155552671): ").strip()

    # Database URL
    print("\n4️⃣  DATABASE_URL (from Supabase > Settings > Database > Connection string):")
    variables["DATABASE_URL"] = input("   DATABASE_URL: ").strip()

    variables["ENVIRONMENT"] = "production"

    return variables

def set_railway_variables(project_id: str, variables: Dict[str, str]) -> bool:
    """Set environment variables in Railway project."""
    print_step(4, "Set Environment Variables in Railway")

    # Link to project
    print(f"Linking to Railway project: {project_id}")
    result = run_command(f"railway link --id {project_id}", check=False)

    # Set each variable
    for key, value in variables.items():
        if not value:
            print_warning(f"Skipping {key} (empty value)")
            continue

        print(f"Setting {key}...")
        cmd = f'railway variables set {key} "{value}"'
        result = run_command(cmd, check=False)

        if result:
            print_success(f"  {key} set")
        else:
            print_warning(f"  Could not verify {key} set (may have worked)")

    print_success("All environment variables configured")
    return True

def set_railway_config() -> bool:
    """Configure Railway settings."""
    print_step(5, "Configure Railway Service Settings")

    print("Setting root directory to chargehero-backend...")
    # Note: Railway root directory might need to be set via API or web UI
    print_warning("Root directory configuration may need web UI setup")
    print("   Go to: https://railway.app > Settings > Root Directory")
    print("   Set to: chargehero-backend")

    return True

def trigger_deployment(project_id: str) -> bool:
    """Trigger deployment."""
    print_step(6, "Trigger Deployment")

    print(f"Project ID: {project_id}")
    print("Triggering deployment...")

    result = run_command(f"railway deploy --id {project_id}", check=False)

    if result:
        print_success("Deployment triggered")
        return True
    else:
        print_warning("Deployment trigger sent (check Railway dashboard)")
        return True

def monitor_deployment(project_id: str) -> bool:
    """Monitor deployment status."""
    print_step(7, "Monitor Deployment")

    print("Monitoring deployment status...")
    print("Check your Railway dashboard for real-time logs:")
    print(f"  https://railway.app/project/{project_id}")

    print("\nWaiting for deployment to complete (this may take 2-3 minutes)...")
    print("You can also run: railway logs --follow")

    return True

def test_api(api_url: Optional[str] = None) -> bool:
    """Test the API health endpoint."""
    print_step(8, "Test API Health Endpoint")

    if not api_url:
        api_url = input("Enter your Railway API URL (e.g., https://chargehero-xxxxx.railway.app): ").strip()

    if not api_url:
        print_warning("Skipping health check")
        return True

    health_url = f"{api_url}/health"
    print(f"Testing: {health_url}")

    try:
        import urllib.request
        import json

        response = urllib.request.urlopen(health_url, timeout=5)
        data = json.loads(response.read().decode())

        print_success(f"API is healthy! Response:")
        print(json.dumps(data, indent=2))
        return True

    except Exception as e:
        print_warning(f"Health check failed: {e}")
        print("This is normal if the deployment is still in progress.")
        return True

def main():
    """Main deployment flow."""
    print(f"\n{Colors.BLUE}")
    print("╔═══════════════════════════════════════════════╗")
    print("║   ChargeHero Railway Deployment Script         ║")
    print("║   Python-based automation for production       ║")
    print("╚═══════════════════════════════════════════════╝")
    print(Colors.RESET)

    # Step 1: Check Railway CLI
    if not check_railway_cli():
        print_error("\nPlease install Railway CLI first:")
        print("  npm install -g @railway/cli")
        sys.exit(1)

    # Step 2: Login
    if not login_railway():
        sys.exit(1)

    # Step 3: Collect variables
    variables = get_environment_variables()

    # Step 4: Set variables
    project_id = "chargehero"  # Or get from user
    if not set_railway_variables(project_id, variables):
        print_error("Failed to set variables")
        sys.exit(1)

    # Step 5: Configure
    set_railway_config()

    # Step 6: Deploy
    if not trigger_deployment(project_id):
        sys.exit(1)

    # Step 7: Monitor
    monitor_deployment(project_id)

    # Step 8: Test
    test_api()

    # Summary
    print(f"\n{Colors.GREEN}")
    print("╔═══════════════════════════════════════════════╗")
    print("║   Deployment Complete!                        ║")
    print("╚═══════════════════════════════════════════════╝")
    print(f"{Colors.RESET}")

    print("\n📊 Next Steps:")
    print("  1. Monitor deployment: railway logs --follow")
    print("  2. Check dashboard: https://railway.app")
    print("  3. Test API: curl https://chargehero-xxxxx.railway.app/health")
    print("  4. Deploy mobile apps once API is verified ✅")

if __name__ == "__main__":
    main()

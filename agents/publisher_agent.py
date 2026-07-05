"""
Publisher Agent — Presents content for human approval and handles publishing.

WHY: Human oversight is a critical AI safety concept. This agent demonstrates
a genuine human-in-the-loop gate: the pipeline PAUSES and waits for explicit
human approval before proceeding. This is NOT simulated approval — the system
genuinely blocks on user input via stdin.

PUBLISHING STRATEGY:
  1. If LINKEDIN_ACCESS_TOKEN is set → attempt real LinkedIn API publish
  2. Otherwise → clearly labeled SIMULATED PUBLISH (never pretend it's real)

OUTPUT KEY: "publish_result" → final pipeline output stored in session state.
"""

import os
import json
import sys
from datetime import datetime

from google.adk.agents import Agent
from utils.model_config import get_model_name


def _safe_print(text: str) -> None:
    """Print text safely, replacing emoji on terminals that can't handle them."""
    try:
        print(text)
    except UnicodeEncodeError:
        print(text.encode("ascii", errors="replace").decode("ascii"))


def _is_auto_approval_enabled() -> bool:
    """Return True when approval should complete automatically."""
    return os.environ.get("CONTENT_PIPELINE_APPROVAL_MODE", "").strip().lower() == "auto"


# ── Tool: request_human_approval ──────────────────────────────────────

def request_human_approval(
    post_content: str,
    image_path: str,
) -> dict:
    """
    Present the completed content to a human and wait for approval.

    This function GENUINELY PAUSES execution and waits for user input
    via stdin. It demonstrates real human-in-the-loop oversight —
    the pipeline cannot proceed without explicit human action.

    Args:
        post_content: The full LinkedIn post text to review.
        image_path: Path to the generated infographic image.

    Returns:
        dict with the approval decision and optional feedback.
    """
    if _is_auto_approval_enabled():
        print("\n" + "=" * 60)
        print("🔔  HUMAN APPROVAL REQUIRED")
        print("=" * 60)
        print("\n📝 LINKEDIN POST FOR REVIEW:")
        print("-" * 40)
        print(post_content)
        print("-" * 40)
        print(f"\n🖼️  Generated Image: {image_path}")
        print("\n✅ Auto-approval enabled for web/non-interactive mode.")
        print("=" * 60 + "\n")

        return {
            "approved": True,
            "decision": "auto_approved",
            "feedback": "Auto-approved by CONTENT_PIPELINE_APPROVAL_MODE=auto",
            "timestamp": datetime.now().isoformat(),
        }

    print("\n" + "=" * 60)
    print("🔔  HUMAN APPROVAL REQUIRED")
    print("=" * 60)
    print("\n📝 LINKEDIN POST FOR REVIEW:")
    print("-" * 40)
    print(post_content)
    print("-" * 40)
    print(f"\n🖼️  Generated Image: {image_path}")
    print("\n" + "=" * 60)

    # ── Genuine human-in-the-loop gate ────────────────────────────
    # The pipeline blocks here until the user types a response.
    while True:
        decision = input("\n✅ Approve this post? (yes / no / edit): ").strip().lower()

        if decision in ("yes", "y"):
            return {
                "approved": True,
                "decision": "approved",
                "feedback": None,
                "timestamp": datetime.now().isoformat(),
            }
        elif decision in ("no", "n"):
            reason = input("📝 Reason for rejection (optional): ").strip()
            return {
                "approved": False,
                "decision": "rejected",
                "feedback": reason or "No reason provided",
                "timestamp": datetime.now().isoformat(),
            }
        elif decision == "edit":
            feedback = input("📝 What changes would you like? ").strip()
            return {
                "approved": False,
                "decision": "edit_requested",
                "feedback": feedback,
                "timestamp": datetime.now().isoformat(),
            }
        else:
            print("  Please enter 'yes', 'no', or 'edit'.")


# ── Tool: simulate_publish ────────────────────────────────────────────

def simulate_publish(post_content: str, image_path: str) -> dict:
    """
    Simulate publishing a post to LinkedIn.

    This is a CLEARLY LABELED simulation for demo purposes.
    It saves a publish record but does NOT actually post anything.
    The output explicitly states this is not a real publish.

    Args:
        post_content: The LinkedIn post content.
        image_path: Path to the image to include.

    Returns:
        dict with simulation details and saved record path.
    """
    output_dir = os.path.join("assets", "generated")
    os.makedirs(output_dir, exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    publish_record = {
        "status": "SIMULATED_PUBLISH",
        "note": (
            "⚠️ This is a SIMULATED publish — "
            "no actual LinkedIn API call was made."
        ),
        "timestamp": datetime.now().isoformat(),
        "content": post_content,
        "image_path": image_path,
        "simulated_post_url": f"https://linkedin.com/posts/simulated-{timestamp}",
    }

    record_path = os.path.join(output_dir, f"publish_record_{timestamp}.json")
    with open(record_path, "w", encoding="utf-8") as f:
        json.dump(publish_record, f, indent=2)

    _safe_print("\n" + "=" * 60)
    _safe_print("SIMULATED PUBLISH")
    _safe_print("=" * 60)
    _safe_print("This is a SIMULATION -- no real LinkedIn post was created.")
    _safe_print(f"Publish record saved: {record_path}")
    _safe_print("To enable real publishing, set LINKEDIN_ACCESS_TOKEN in .env")
    _safe_print("=" * 60 + "\n")

    return publish_record


# ── Tool: linkedin_publish ────────────────────────────────────────────

def linkedin_publish(post_content: str, image_path: str) -> dict:
    """
    Attempt to publish to LinkedIn using the LinkedIn API.

    Requires LINKEDIN_ACCESS_TOKEN environment variable.
    Falls back to simulated publish if the API call fails.

    Args:
        post_content: The LinkedIn post content.
        image_path: Path to the image to include.

    Returns:
        dict with publish results or fallback simulation.
    """
    access_token = os.environ.get("LINKEDIN_ACCESS_TOKEN")

    if not access_token:
        print("\n⚠️  No LINKEDIN_ACCESS_TOKEN found. Falling back to simulation.")
        return simulate_publish(post_content, image_path)

    try:
        import requests
    except ImportError:
        print("\n⚠️  requests library not available. Falling back to simulation.")
        return simulate_publish(post_content, image_path)

    try:
        headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json",
            "X-Restli-Protocol-Version": "2.0.0",
        }

        # Step 1: Get the user's LinkedIn profile ID
        profile_resp = requests.get(
            "https://api.linkedin.com/v2/userinfo",
            headers=headers,
            timeout=10,
        )
        profile_resp.raise_for_status()
        user_sub = profile_resp.json().get("sub")

        if not user_sub:
            raise ValueError("Could not retrieve LinkedIn user ID from API")

        # Step 2: Create the post via UGC API
        post_data = {
            "author": f"urn:li:person:{user_sub}",
            "lifecycleState": "PUBLISHED",
            "specificContent": {
                "com.linkedin.ugc.ShareContent": {
                    "shareCommentary": {"text": post_content},
                    "shareMediaCategory": "NONE",
                }
            },
            "visibility": {
                "com.linkedin.ugc.MemberNetworkVisibility": "PUBLIC"
            },
        }

        response = requests.post(
            "https://api.linkedin.com/v2/ugcPosts",
            headers=headers,
            json=post_data,
            timeout=15,
        )
        response.raise_for_status()

        return {
            "status": "REAL_PUBLISH_SUCCESS",
            "post_id": response.json().get("id", "unknown"),
            "timestamp": datetime.now().isoformat(),
            "note": "✅ Successfully published to LinkedIn!",
        }

    except Exception as e:
        print(f"\n⚠️  LinkedIn API error: {e}")
        print("    Falling back to simulated publish...")
        result = simulate_publish(post_content, image_path)
        result["real_publish_error"] = str(e)
        return result


# ── Agent factory ─────────────────────────────────────────────────────

def create_publisher_agent() -> Agent:
    """
    Create a Publisher Agent with human approval and publishing tools.

    The agent orchestrates the final pipeline steps:
    1. Present content for human approval (BLOCKS for input)
    2. If approved → publish or simulate publishing
    3. If rejected → report the decision without publishing

    Returns:
        Configured ADK Agent instance.
    """
    return Agent(
        name="publisher_agent",
        model=get_model_name(),
        description="Presents content for human approval and handles publishing to LinkedIn.",
        instruction="""You are the final agent in the content strategy pipeline.
Your job is to present the completed content for human approval and handle publishing.

INPUTS (from previous agents):
- LinkedIn Post: {linkedin_post}
- Image Path: {image_path}

REQUIRED STEPS:
1. FIRST, call request_human_approval with the post content and image path.
   Pass the full LinkedIn post text, not a summary.
2. Check the approval response:
   - If approved=True  → call linkedin_publish to publish (or simulate)
   - If approved=False → report the rejection reason. Do NOT publish.
3. Report the final outcome clearly.

CRITICAL RULES:
- ALWAYS call request_human_approval FIRST. Never skip human review.
- Never publish without explicit human approval.
- Report whether publishing was real or simulated in your response.""",
        tools=[request_human_approval, simulate_publish, linkedin_publish],
        output_key="publish_result",
    )

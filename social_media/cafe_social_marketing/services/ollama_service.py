import json
import urllib.error
import urllib.request


OLLAMA_URL = "http://host.docker.internal:11434/api/chat"
OLLAMA_MODEL = "qwen2.5-coder:7b"


def review_social_post(post_data):
    system_prompt = """
You are a social media content reviewer for a multi-branch cafe chain.

Your job is ONLY to review writing quality and communication.

Review:
- tone
- clarity
- professionalism
- overly aggressive wording
- potentially misleading or unsupported marketing claims
- whether important campaign information is communicated clearly

Do NOT decide whether branch, discount, campaign dates, or social accounts
are factually valid. Odoo handles those using deterministic business rules.

Return ONLY valid JSON using exactly this structure:

{
    "overall_status": "Good" or "Needs Improvement",
    "tone": "short assessment",
    "clarity": "short assessment",
    "potential_issues": ["issue 1", "issue 2"],
    "suggested_rewrite": "improved social post"
}
"""

    user_prompt = f"""
Review this social media post.

POST:
{post_data.get("message", "")}

BUSINESS CONTEXT:
Branch: {post_data.get("branch", "")}
Campaign: {post_data.get("campaign", "")}
Product: {post_data.get("product", "")}
Campaign Discount: {post_data.get("discount", "")}
Campaign Start: {post_data.get("start_date", "")}
Campaign End: {post_data.get("end_date", "")}
Social Accounts: {post_data.get("social_accounts", "")}
"""

    payload = {
        "model": OLLAMA_MODEL,
        "messages": [
            {
                "role": "system",
                "content": system_prompt,
            },
            {
                "role": "user",
                "content": user_prompt,
            },
        ],
        "stream": False,
        "format": "json",
    }

    request = urllib.request.Request(
        OLLAMA_URL,
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Content-Type": "application/json",
        },
        method="POST",
    )

    try:
        with urllib.request.urlopen(
            request,
            timeout=90,
        ) as response:
            raw_response = response.read().decode("utf-8")

    except urllib.error.URLError as error:
        raise RuntimeError(
            f"Could not connect to Ollama: {error}"
        ) from error

    except TimeoutError as error:
        raise RuntimeError(
            "Ollama took too long to respond."
        ) from error

    try:
        ollama_response = json.loads(raw_response)

        content = ollama_response["message"]["content"]

        result = json.loads(content)

    except (
        json.JSONDecodeError,
        KeyError,
        TypeError,
    ) as error:
        raise RuntimeError(
            "Ollama returned an invalid AI review response."
        ) from error

    return result
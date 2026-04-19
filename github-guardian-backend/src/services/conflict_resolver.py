from openai import AsyncOpenAI
from src.core.config import settings

# Same client as other services
client = AsyncOpenAI(api_key=settings.openai_api_key)

async def resolve_file_conflict(file_name: str, remote_content: str, local_content: str) -> str:
    """
    Uses OpenAI to perform a logical Git merge of the local changes directly into the remote
    version of a file, resolving any potential merge conflicts intelligently.
    """
    prompt = f"""
You are an expert Git Merge Agent. Your job is to resolve a conflict between the current remote version of a file and the new local version that the user is trying to push.

File: {file_name}

=== REMOTE CONTENT (Currently on GitHub) ===
{remote_content}

=== LOCAL CONTENT (What user wants to push) ===
{local_content}

Instructions:
1. Understand the logical intent of the local changes compared to the remote.
2. Produce a single, complete merged file.
3. If there are truly incompatible logical changes, output the local content. However, strive to integrate structural changes.
4. DO NOT include any git conflict markers (<<<<<<<, =======, >>>>>>>).
5. DO NOT wrap the output in markdown code blocks (```python ... ```). Output the RAW plain text only, as this will be pushed directly to GitHub.
"""

    try:
        response = await client.chat.completions.create(
            model="gpt-4o",  # Can handle complexity well
            messages=[
                {"role": "system", "content": "You are a git merge conflict resolver bot."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.2, # Low temperature for more deterministic/safe merging
            max_tokens=4000
        )
        resolved_content = response.choices[0].message.content.strip()

        # Just in case the LLM wrapped it in markdown codeblocks anyway
        if resolved_content.startswith("```"):
            lines = resolved_content.split("\n")
            if len(lines) > 2 and lines[0].startswith("```") and lines[-1] == "```":
                resolved_content = "\n".join(lines[1:-1])

        return resolved_content
    except Exception as e:
        print(f"Conflict resolution failed for {file_name}: {e}")
        # Fallback to local content (overwrite remote) if AI fails
        return local_content

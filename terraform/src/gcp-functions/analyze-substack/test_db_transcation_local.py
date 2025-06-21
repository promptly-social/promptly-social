import json
import sys
import asyncio
from main import get_supabase_client, update_analysis_results


async def test_db_transcation(user_id: str):
    with open("test-output.json", "r") as f:
        analysis_result = json.load(f)

    supabase = get_supabase_client()
    await update_analysis_results(
        supabase,
        user_id,
        analysis_result,
    )


def main():
    if len(sys.argv) != 2:
        print("Usage: python test_db_transcation_local.py [user_id]")
        print("Example: python test_db_transcation_local.py 123")
        sys.exit(1)

    user_id = sys.argv[1]

    asyncio.run(test_db_transcation(user_id))


if __name__ == "__main__":
    main()

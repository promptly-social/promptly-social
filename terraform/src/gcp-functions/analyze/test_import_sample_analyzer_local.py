#!/usr/bin/env python3
"""
Local testing script for the Import Sample analysis function.

Usage:
    python test_import_sample_analyzer_local.py [--sample-file path/to/file.txt]

Example:
    python test_import_sample_analyzer_local.py
    python test_import_sample_analyzer_local.py --sample-file my_writing_sample.txt
"""

import os
import sys
import json
import argparse
from import_sample_analyzer import ImportSampleAnalyzer


# Sample writing text for testing
SAMPLE_WRITING_TEXT = """
The future of artificial intelligence isn't just about building smarter machines—it's about creating systems that can genuinely understand and collaborate with humans. As someone who's spent years in the tech industry, I've seen firsthand how AI can either amplify human capabilities or create new barriers.

What excites me most is the potential for AI to democratize expertise. Think about it: complex financial analysis, medical diagnosis, or legal research—these used to require years of specialized training. Now, we're building tools that can make these insights accessible to everyone.

But here's the thing that keeps me up at night: we're moving so fast that we're forgetting to ask the hard questions. Who benefits from these systems? What happens to the jobs they replace? How do we ensure they're fair and unbiased?

I believe the answer lies in building AI with intention, not just innovation. We need diverse teams, ethical frameworks, and a commitment to transparency. The companies that will thrive in the next decade aren't just those with the best algorithms—they're the ones that can build trust.

The revolution isn't coming. It's here. And it's up to us to make sure it lifts everyone up, not just the lucky few.
"""

SAMPLE_BLOG_POST = """
Why I Deleted All My Social Media Apps (And You Should Too)

For the past month, I've been living without Instagram, Twitter, TikTok, or Facebook on my phone. The results have been nothing short of transformative.

It started as an experiment. I was tired of the constant ping of notifications, the mindless scrolling, the weird anxiety I felt when I couldn't check my feeds. Sound familiar?

Here's what I discovered:

**My attention span returned.** Seriously. I can read entire articles again without feeling the urge to check my phone. I finished three books this month—more than I read in the previous six months combined.

**I sleep better.** No more late-night Instagram rabbit holes. No more lying in bed scrolling through Twitter drama. My brain actually gets to rest.

**I'm more present.** Conversations feel deeper. I notice things—the way light hits a coffee cup, how my dog stretches when she wakes up, the satisfaction of completing a task without documenting it.

**I'm more creative.** Without constant input from others, my own thoughts have room to breathe and grow. I'm writing more, cooking more, exploring ideas that feel genuinely mine.

Look, I'm not saying social media is evil. It connects us, inspires us, and can be a force for good. But the way we're using it—constantly, compulsively, without intention—is breaking something fundamental about how we think and feel.

Try it for a week. Delete the apps (you can always reinstall them). Notice what comes up. The boredom, the FOMO, the phantom vibrations. Then notice what comes after: space, clarity, and maybe—just maybe—a version of yourself you forgot existed.

Your brain will thank you.
"""

TECHNICAL_WRITING_SAMPLE = """
Implementing Effective Database Indexing Strategies

Database performance optimization is critical for scalable applications, and indexing represents one of the most impactful techniques available to developers. However, poorly implemented indexes can actually degrade performance, making it essential to understand when and how to apply them effectively.

## Understanding Index Types

B-tree indexes, the most common type, excel at equality and range queries but consume significant storage space. Hash indexes offer faster equality lookups but don't support range queries. Bitmap indexes work well for low-cardinality data but require careful consideration in high-write environments.

## Query Pattern Analysis

Before creating indexes, analyze your query patterns. Use EXPLAIN ANALYZE to understand execution plans. Look for table scans on large datasets, expensive sort operations, and inefficient joins. These indicators suggest where indexes might provide the greatest benefit.

## Index Maintenance Overhead

Every index requires maintenance during INSERT, UPDATE, and DELETE operations. For write-heavy applications, excessive indexing can significantly impact performance. Monitor index usage statistics and remove unused indexes that only add overhead.

## Composite Index Optimization

When creating multi-column indexes, column order matters significantly. Place highly selective columns first, followed by less selective ones. This approach maximizes the index's effectiveness for partial key lookups.

## Monitoring and Iteration

Database optimization is an iterative process. Regularly review slow query logs, monitor index usage statistics, and adjust your indexing strategy as application requirements evolve. Tools like pg_stat_user_indexes in PostgreSQL provide valuable insights into index effectiveness.

Remember: premature optimization is the root of all evil, but so is ignoring performance until it becomes a problem. Find the balance that works for your specific use case.
"""


def test_individual_methods(analyzer: ImportSampleAnalyzer, sample_text: str):
    """Test individual methods of the analyzer."""
    print("\n🧪 Testing Individual Methods:")
    print("=" * 50)

    # Test writing style analysis
    print("\n📝 Testing Writing Style Analysis...")
    try:
        writing_style = analyzer._analyze_writing_style_from_sample(sample_text)
        print(f"✅ Writing style analysis completed ({len(writing_style)} characters)")
        print(f"Preview: {writing_style[:200]}...")
    except Exception as e:
        print(f"❌ Writing style analysis failed: {e}")

    # Test topic analysis
    print("\n🏷️ Testing Topic Analysis...")
    try:
        topics = analyzer._analyze_topics_from_sample(sample_text)
        print(f"✅ Topic analysis completed ({len(topics)} topics found)")
        print(f"Topics: {', '.join(topics)}")
    except Exception as e:
        print(f"❌ Topic analysis failed: {e}")

    # Test bio creation
    print("\n👤 Testing Bio Creation...")
    try:
        current_bio = "I'm a professional who likes to write about technology and life."
        bio = analyzer._create_user_bio_from_sample(sample_text, current_bio)
        print(f"✅ Bio creation completed ({len(bio)} characters)")
        print(f"Bio: {bio}")
    except Exception as e:
        print(f"❌ Bio creation failed: {e}")


def test_comprehensive_analysis(
    analyzer: ImportSampleAnalyzer, sample_text: str, current_bio: str = ""
):
    """Test the comprehensive analysis function."""
    print("\n🔍 Testing Comprehensive Analysis:")
    print("=" * 50)

    content_to_analyze = ["writing_style"]

    try:
        result = analyzer.analyze_import_sample(
            sample_text, current_bio, content_to_analyze
        )

        print("✅ Comprehensive analysis completed successfully!")
        print("\n📊 Results Summary:")
        print(f"   • Writing style: {len(result.get('writing_style', ''))} characters")
        print(f"   • Topics found: {len(result.get('topics', []))}")
        print(f"   • Bio: {len(result.get('bio', ''))} characters")
        print(f"   • Websites: {len(result.get('websites', []))}")

        print("\n🔍 Detailed Results:")
        print("-" * 30)

        if result.get("writing_style"):
            print(f"\n📝 Writing Style:\n{result['writing_style']}")

        if result.get("topics"):
            print(f"\n🏷️ Topics: {', '.join(result['topics'])}")

        if result.get("bio"):
            print(f"\n👤 Bio:\n{result['bio']}")

        print("\n🔍 Full Analysis (JSON):")
        print(json.dumps(result, indent=2))

        return result

    except Exception as e:
        print(f"❌ Comprehensive analysis failed: {e}")
        import traceback

        traceback.print_exc()
        return None


def test_different_writing_styles():
    """Test the analyzer with different types of writing."""
    print("\n🎭 Testing Different Writing Styles:")
    print("=" * 50)

    analyzer = ImportSampleAnalyzer(openrouter_api_key=os.getenv("OPENROUTER_API_KEY"))

    test_cases = [
        ("Personal/Reflective", SAMPLE_WRITING_TEXT),
        ("Blog Post", SAMPLE_BLOG_POST),
        ("Technical Writing", TECHNICAL_WRITING_SAMPLE),
    ]

    for style_name, sample_text in test_cases:
        print(f"\n--- Testing {style_name} ---")
        try:
            writing_style = analyzer._analyze_writing_style_from_sample(sample_text)
            topics = analyzer._analyze_topics_from_sample(sample_text)

            print(f"✅ {style_name} analysis completed")
            print(
                f"   Topics: {', '.join(topics[:3])}{'...' if len(topics) > 3 else ''}"
            )
            print(f"   Style preview: {writing_style[:150]}...")

        except Exception as e:
            print(f"❌ {style_name} analysis failed: {e}")


def load_sample_from_file(file_path: str) -> str:
    """Load writing sample from a file."""
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            return f.read()
    except FileNotFoundError:
        print(f"❌ File not found: {file_path}")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Error reading file: {e}")
        sys.exit(1)


def main():
    parser = argparse.ArgumentParser(
        description="Test the Import Sample Analyzer locally"
    )
    parser.add_argument(
        "--sample-file", help="Path to a text file containing the writing sample"
    )
    parser.add_argument(
        "--test-all",
        action="store_true",
        help="Run all test cases including different writing styles",
    )
    parser.add_argument(
        "--methods-only", action="store_true", help="Test individual methods only"
    )

    args = parser.parse_args()

    # Check for required environment variables
    if not os.getenv("OPENROUTER_API_KEY"):
        print("❌ Error: OPENROUTER_API_KEY environment variable is required")
        print("Please set it in your environment or .env file")
        sys.exit(1)

    print("🚀 Import Sample Analyzer Local Test")
    print("=" * 50)

    # Determine which sample text to use
    if args.sample_file:
        print(f"📁 Loading writing sample from: {args.sample_file}")
        sample_text = load_sample_from_file(args.sample_file)
        print(f"✅ Loaded {len(sample_text)} characters from file")
    else:
        print("📄 Using default sample text")
        sample_text = SAMPLE_WRITING_TEXT

    # Initialize analyzer
    analyzer = ImportSampleAnalyzer(openrouter_api_key=os.getenv("OPENROUTER_API_KEY"))

    # Run tests based on arguments
    if args.test_all:
        test_different_writing_styles()

    if args.methods_only:
        test_individual_methods(analyzer, sample_text)
    else:
        # Run comprehensive test
        current_bio = (
            "I'm a tech professional with a passion for writing and innovation."
        )
        result = test_comprehensive_analysis(analyzer, sample_text, current_bio)

        if result and not args.methods_only:
            test_individual_methods(analyzer, sample_text)

    print("\n✨ Test completed!")


if __name__ == "__main__":
    main()

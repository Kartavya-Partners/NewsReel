"""Main CLI entry point for the AI News Explainer."""

import argparse
import sys
from pathlib import Path
from loguru import logger
from workflows.news_video_workflow import NewsVideoWorkflow
import json


def setup_logging(level: str = "INFO"):
    """Setup logging configuration."""
    logger.remove()
    logger.add(
        sys.stderr,
        format="<green>{time:HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan> - <level>{message}</level>",
        level=level
    )
    logger.add(
        "logs/app.log",
        rotation="10 MB",
        retention="7 days",
        level=level
    )


def main():
    """Main CLI function."""
    parser = argparse.ArgumentParser(
        description="AI News Explainer Video Generator"
    )
    
    parser.add_argument(
        "--topic",
        type=str,
        required=True,
        help="News topic to search for (e.g., 'AI in Healthcare')"
    )
    
    parser.add_argument(
        "--category",
        type=str,
        default=None,
        help="News category (e.g., 'technology', 'politics', 'sports', 'Geography', 'Environment', 'Health', 'Education', 'Geopolitics', 'Economy', 'Business')"
    )
    
    parser.add_argument(
        "--config",
        type=str,
        default="config/settings.yaml",
        help="Path to configuration file"
    )
    
    parser.add_argument(
        "--output",
        type=str,
        default="output/result.json",
        help="Output file for results"
    )
    
    parser.add_argument(
        "--log-level",
        type=str,
        default="INFO",
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
        help="Logging level"
    )
    
    parser.add_argument(
        "--generate-video",
        action="store_true",
        help="Generate video from scene plan (requires moviepy and gTTS)"
    )
    
    args = parser.parse_args()
    
    # Setup logging
    setup_logging(args.log_level)
    
    logger.info("=" * 60)
    logger.info("AI News Explainer Video Generator")
    logger.info("=" * 60)
    
    try:
        # Initialize workflow
        workflow = NewsVideoWorkflow(
            config_path=args.config,
            generate_video=args.generate_video
        )
        
        # Run workflow
        result = workflow.run(
            topic=args.topic,
            category=args.category
        )
        
        # Save results
        output_path = Path(args.output)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(result, f, indent=2, ensure_ascii=False)
        
        logger.success(f"Results saved to: {output_path}")
        
        # Print summary
        print("\n" + "=" * 60)
        print("WORKFLOW COMPLETED SUCCESSFULLY")
        print("=" * 60)
        print(f"\nTopic: {result['topic']}")
        print(f"\nSummary:\n{result['summary']}")
        print(f"\nNarration:\n{result['narration']}")
        print(f"\nScenes: {len(result['scene_plan'])}")
        
        # Show video path if generated
        if 'video_path' in result:
            print(f"\n✅ VIDEO GENERATED: {result['video_path']}")
        
        print(f"\nFull results saved to: {output_path}")
        print("=" * 60)
        
    except Exception as e:
        logger.error(f"Workflow failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()

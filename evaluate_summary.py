"""
Evaluate summary quality against raw fetched articles.

This script compares the AI-generated summary with the original source articles
to assess how well the summary preserves main points, facts, and context.
"""

import json
import argparse
from pathlib import Path
from typing import Dict, List, Any
from datetime import datetime


class SummaryEvaluator:
    """Evaluates summary quality against source articles."""
    
    def __init__(self, result_path: str, articles_path: str):
        """
        Initialize evaluator.
        
        Args:
            result_path: Path to result.json
            articles_path: Path to raw_articles.json
        """
        self.result = self._load_json(result_path)
        self.articles = self._load_json(articles_path)
        self.summary = self.result.get('summary', '')
        
    def _load_json(self, path: str) -> Dict:
        """Load JSON file."""
        with open(path, 'r', encoding='utf-8') as f:
            return json.load(f)
    
    def _extract_entities(self, text: str) -> set:
        """
        Extract key entities from text (simple word-based extraction).
        
        In production, this would use NER (Named Entity Recognition).
        For now, we extract capitalized words and phrases.
        """
        words = text.split()
        entities = set()
        
        # Extract capitalized words (potential proper nouns)
        for word in words:
            # Remove punctuation
            clean_word = word.strip('.,;:!?"\'()[]{}')
            # Check if capitalized and longer than 2 chars
            if clean_word and clean_word[0].isupper() and len(clean_word) > 2:
                # Skip common words
                if clean_word.lower() not in ['the', 'and', 'but', 'for', 'with', 'from', 'this', 'that']:
                    entities.add(clean_word)
        
        return entities
    
    def _extract_key_facts(self, articles: List[Dict]) -> List[str]:
        """Extract key facts from articles (titles and first sentences)."""
        facts = []
        
        for article in articles:
            # Add title as a key fact
            title = article.get('title', '').strip()
            if title:
                facts.append(title)
            
            # Add first sentence of content as key fact
            content = article.get('content', '').strip()
            if content:
                # Get first sentence (rough approximation)
                first_sentence = content.split('.')[0].strip()
                if first_sentence and len(first_sentence) > 20:
                    facts.append(first_sentence)
        
        return facts
    
    def evaluate_entity_preservation(self) -> Dict[str, Any]:
        """Evaluate how well entities are preserved from articles to summary."""
        # Extract entities from articles
        article_entities = set()
        for article in self.articles:
            title = article.get('title', '')
            content = article.get('content', '')
            article_text = f"{title} {content}"
            article_entities.update(self._extract_entities(article_text))
        
        # Extract entities from summary
        summary_entities = self._extract_entities(self.summary)
        
        # Calculate preservation
        if not article_entities:
            return {
                'score': 10,
                'article_entities': 0,
                'summary_entities': 0,
                'preserved': 0,
                'preservation_rate': 1.0,
                'missing_entities': [],
                'note': 'No entities found in articles'
            }
        
        preserved = article_entities.intersection(summary_entities)
        missing = article_entities - summary_entities
        
        preservation_rate = len(preserved) / len(article_entities) if article_entities else 0
        score = min(10, int(preservation_rate * 10))
        
        return {
            'score': score,
            'article_entities': len(article_entities),
            'summary_entities': len(summary_entities),
            'preserved': len(preserved),
            'preservation_rate': preservation_rate,
            'missing_entities': sorted(list(missing))[:10],  # Top 10 missing
            'preserved_entities': sorted(list(preserved))[:10]  # Top 10 preserved
        }
    
    def evaluate_completeness(self) -> Dict[str, Any]:
        """Evaluate how complete the summary is compared to articles."""
        # Extract key facts from articles
        article_facts = self._extract_key_facts(self.articles)
        
        # Check how many facts are mentioned in summary
        facts_in_summary = 0
        missing_facts = []
        preserved_facts = []
        
        for fact in article_facts:
            # Simple substring check (in production, use semantic similarity)
            # Check for key words from fact in summary
            fact_words = set(fact.lower().split())
            summary_words = set(self.summary.lower().split())
            
            # If at least 50% of fact words are in summary, consider it preserved
            overlap = fact_words.intersection(summary_words)
            if len(overlap) >= len(fact_words) * 0.4:  # 40% threshold
                facts_in_summary += 1
                preserved_facts.append(fact)
            else:
                missing_facts.append(fact)
        
        completeness_rate = facts_in_summary / len(article_facts) if article_facts else 0
        score = min(10, int(completeness_rate * 10))
        
        return {
            'score': score,
            'total_facts': len(article_facts),
            'facts_in_summary': facts_in_summary,
            'completeness_rate': completeness_rate,
            'missing_facts': missing_facts[:5],  # Top 5 missing
            'preserved_facts': preserved_facts[:5]  # Top 5 preserved
        }
    
    def evaluate_factual_accuracy(self) -> Dict[str, Any]:
        """
        Evaluate factual accuracy (basic check for contradictions).
        
        Note: This is a simplified version. Full implementation would use
        fact-checking models or manual verification.
        """
        # For now, we assume no contradictions if entities are preserved
        # In production, this would use fact-checking models
        
        # Simple heuristic: if summary is much longer than articles, might have hallucinations
        total_article_length = sum(len(a.get('content', '')) for a in self.articles)
        summary_length = len(self.summary)
        
        # If summary is longer than total articles, might be adding false info
        if summary_length > total_article_length * 1.5:
            score = 6
            note = "Summary is significantly longer than source articles - may contain added information"
        else:
            score = 9
            note = "Summary length is reasonable relative to source articles"
        
        return {
            'score': score,
            'total_article_length': total_article_length,
            'summary_length': summary_length,
            'length_ratio': summary_length / total_article_length if total_article_length > 0 else 0,
            'note': note
        }
    
    def evaluate_context_preservation(self) -> Dict[str, Any]:
        """Evaluate how well context is preserved."""
        # Check if article URLs/sources are diverse
        sources = set()
        for article in self.articles:
            url = article.get('url', '')
            if url:
                # Extract domain
                domain = url.split('/')[2] if len(url.split('/')) > 2 else url
                sources.add(domain)
        
        # If multiple sources, good context
        # If summary mentions multiple perspectives, good context preservation
        
        multi_source = len(sources) > 1
        
        # Simple heuristic: check for words indicating synthesis
        synthesis_words = ['according to', 'reported', 'sources', 'multiple', 'various', 'several']
        has_synthesis = any(word in self.summary.lower() for word in synthesis_words)
        
        if multi_source and has_synthesis:
            score = 9
            note = "Multiple sources synthesized with attribution"
        elif multi_source:
            score = 7
            note = "Multiple sources used but limited synthesis indicators"
        else:
            score = 6
            note = "Limited source diversity or synthesis"
        
        return {
            'score': score,
            'num_sources': len(sources),
            'sources': sorted(list(sources)),
            'has_synthesis_language': has_synthesis,
            'note': note
        }
    
    def evaluate(self) -> Dict[str, Any]:
        """Run full evaluation and generate report."""
        print("=" * 60)
        print("SUMMARY EVALUATION")
        print("=" * 60)
        print(f"\nEvaluating summary against {len(self.articles)} source articles...")
        
        # Run all evaluations
        entity_eval = self.evaluate_entity_preservation()
        completeness_eval = self.evaluate_completeness()
        accuracy_eval = self.evaluate_factual_accuracy()
        context_eval = self.evaluate_context_preservation()
        
        # Calculate overall score (weighted average)
        overall_score = int(
            entity_eval['score'] * 0.3 +
            completeness_eval['score'] * 0.3 +
            accuracy_eval['score'] * 0.2 +
            context_eval['score'] * 0.2
        )
        
        # Generate justification
        justification = self._generate_justification(
            overall_score,
            entity_eval,
            completeness_eval,
            accuracy_eval,
            context_eval
        )
        
        # Compile results
        evaluation = {
            'score': overall_score,
            'timestamp': datetime.now().isoformat(),
            'total_articles': len(self.articles),
            'summary_length': len(self.summary),
            'evaluation': {
                'entity_preservation': entity_eval['score'],
                'completeness': completeness_eval['score'],
                'factual_accuracy': accuracy_eval['score'],
                'context_preservation': context_eval['score']
            },
            'details': {
                'entity_preservation': entity_eval,
                'completeness': completeness_eval,
                'factual_accuracy': accuracy_eval,
                'context_preservation': context_eval
            },
            'justification': justification
        }
        
        return evaluation
    
    def _generate_justification(self, overall_score, entity_eval, completeness_eval, 
                                accuracy_eval, context_eval) -> str:
        """Generate detailed justification for the score."""
        lines = []
        
        lines.append(f"Overall Score: {overall_score}/10")
        lines.append("")
        
        # Entity preservation
        lines.append(f"Entity Preservation ({entity_eval['score']}/10):")
        lines.append(f"  - {entity_eval['preserved']}/{entity_eval['article_entities']} entities preserved ({entity_eval['preservation_rate']:.1%})")
        if entity_eval.get('missing_entities'):
            lines.append(f"  - Missing entities: {', '.join(entity_eval['missing_entities'][:5])}")
        lines.append("")
        
        # Completeness
        lines.append(f"Completeness ({completeness_eval['score']}/10):")
        lines.append(f"  - {completeness_eval['facts_in_summary']}/{completeness_eval['total_facts']} key facts included ({completeness_eval['completeness_rate']:.1%})")
        if completeness_eval.get('missing_facts'):
            lines.append(f"  - Missing facts: {len(completeness_eval['missing_facts'])} facts not fully covered")
        lines.append("")
        
        # Accuracy
        lines.append(f"Factual Accuracy ({accuracy_eval['score']}/10):")
        lines.append(f"  - {accuracy_eval['note']}")
        lines.append(f"  - Length ratio: {accuracy_eval['length_ratio']:.2f}")
        lines.append("")
        
        # Context
        lines.append(f"Context Preservation ({context_eval['score']}/10):")
        lines.append(f"  - {context_eval['note']}")
        lines.append(f"  - Sources: {context_eval['num_sources']}")
        lines.append("")
        
        # Overall assessment
        if overall_score >= 9:
            lines.append("✅ EXCELLENT: Summary excellently preserves article information")
        elif overall_score >= 7:
            lines.append("✅ GOOD: Summary adequately preserves most article information")
        elif overall_score >= 5:
            lines.append("⚠️ FAIR: Summary preserves some information but has notable gaps")
        else:
            lines.append("❌ POOR: Summary has significant gaps or inaccuracies")
        
        return "\n".join(lines)


def main():
    """Main CLI function."""
    parser = argparse.ArgumentParser(
        description="Evaluate summary quality against raw articles"
    )
    
    parser.add_argument(
        '--result',
        type=str,
        default='output/result.json',
        help='Path to result.json file'
    )
    
    parser.add_argument(
        '--articles',
        type=str,
        default='output/raw_articles.json',
        help='Path to raw_articles.json file'
    )
    
    parser.add_argument(
        '--output',
        type=str,
        default='output/summary_evaluation.json',
        help='Path to save evaluation results'
    )
    
    args = parser.parse_args()
    
    # Check files exist
    if not Path(args.result).exists():
        print(f"❌ Error: {args.result} not found")
        return
    
    if not Path(args.articles).exists():
        print(f"❌ Error: {args.articles} not found")
        print(f"   Make sure to run the workflow first to generate raw_articles.json")
        return
    
    # Run evaluation
    evaluator = SummaryEvaluator(args.result, args.articles)
    evaluation = evaluator.evaluate()
    
    # Save results
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(evaluation, f, indent=2, ensure_ascii=False)
    
    # Print results
    print("\n" + "=" * 60)
    print("EVALUATION COMPLETE")
    print("=" * 60)
    print(f"\n{evaluation['justification']}")
    print(f"\nDetailed results saved to: {output_path}")
    print("=" * 60)


if __name__ == '__main__':
    main()

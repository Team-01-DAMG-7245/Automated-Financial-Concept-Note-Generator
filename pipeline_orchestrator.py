"""
Pipeline Orchestrator for AURELIA
Coordinates all processing steps from PDF to vector database
"""

import json
import os
import sys
import time
import argparse
from pathlib import Path
from typing import Dict, List, Any, Optional
from datetime import datetime
import logging

# Load environment variables
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / 'src'))

from chunkers.base_chunker import Chunk
from embeddings.embedder import Embedder
from storage.pinecone_store import PineconeStore

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('pipeline.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class PipelineOrchestrator:
    """
    Main pipeline orchestrator for AURELIA
    Coordinates PDF parsing, chunking, embedding, and storage
    """
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize pipeline orchestrator
        
        Args:
            config: Configuration dictionary
        """
        self.config = config
        self.start_time = time.time()
        
        # Pipeline state
        self.state = {
            'pdf_parsed': False,
            'markdown_generated': False,
            'chunks_created': False,
            'embeddings_generated': False,
            'vectors_stored': False,
            'checkpoint_file': Path('outputs/pipeline_checkpoint.json')
        }
        
        # Metrics
        self.metrics = {
            'pdf_pages': 0,
            'markdown_size': 0,
            'chunks_created': 0,
            'embeddings_generated': 0,
            'vectors_stored': 0,
            'total_tokens': 0,
            'total_cost': 0.0,
            'pipeline_time': 0.0,
            'step_times': {}
        }
        
        # Load checkpoint if exists
        if self.config.get('resume') and self.state['checkpoint_file'].exists():
            self.load_checkpoint()
    
    def load_checkpoint(self):
        """Load pipeline state from checkpoint"""
        try:
            with open(self.state['checkpoint_file'], 'r') as f:
                checkpoint = json.load(f)
            
            self.state.update(checkpoint.get('state', {}))
            self.metrics.update(checkpoint.get('metrics', {}))
            
            logger.info(f"Loaded checkpoint from {self.state['checkpoint_file']}")
            logger.info(f"Resuming from: {self.get_current_stage()}")
            
        except Exception as e:
            logger.error(f"Failed to load checkpoint: {e}")
    
    def save_checkpoint(self):
        """Save pipeline state to checkpoint"""
        try:
            checkpoint = {
                'timestamp': datetime.now().isoformat(),
                'state': self.state,
                'metrics': self.metrics
            }
            
            with open(self.state['checkpoint_file'], 'w') as f:
                json.dump(checkpoint, f, indent=2)
            
            logger.info(f"Checkpoint saved to {self.state['checkpoint_file']}")
            
        except Exception as e:
            logger.error(f"Failed to save checkpoint: {e}")
    
    def get_current_stage(self) -> str:
        """Get current pipeline stage"""
        if not self.state['pdf_parsed']:
            return "PDF Parsing"
        elif not self.state['markdown_generated']:
            return "Markdown Generation"
        elif not self.state['chunks_created']:
            return "Chunking"
        elif not self.state['embeddings_generated']:
            return "Embedding Generation"
        elif not self.state['vectors_stored']:
            return "Vector Storage"
        else:
            return "Complete"
    
    def run_pdf_parser(self) -> bool:
        """
        Pipeline 1: PDF → Markdown
        Run PDF parser and generate markdown
        """
        if self.state['pdf_parsed'] and self.state['markdown_generated']:
            logger.info("PDF already parsed and markdown generated, skipping...")
            return True
        
        logger.info("=" * 80)
        logger.info("PIPELINE 1: PDF → MARKDOWN")
        logger.info("=" * 80)
        
        step_start = time.time()
        
        try:
            # Import parser
            from parse_fintbx import parse_fintbx_pdf
            
            # Run parser
            logger.info(f"Parsing PDF: {self.config['pdf_file']}")
            parse_fintbx_pdf(
                pdf_path=self.config['pdf_file'],
                output_dir=self.config['output_dir']
            )
            
            self.state['pdf_parsed'] = True
            self.save_checkpoint()
            
            # Generate markdown
            logger.info("Generating markdown...")
            from markdown_generator import generate_markdown
            
            markdown_file = Path(self.config['output_dir']) / 'fintbx_complete.md'
            generate_markdown(
                parsed_dir=self.config['output_dir'],
                output_file=markdown_file
            )
            
            # Validate output
            if markdown_file.exists():
                with open(markdown_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                self.metrics['markdown_size'] = len(content)
                self.state['markdown_generated'] = True
                self.save_checkpoint()
                
                logger.info(f"[OK] Markdown generated: {markdown_file}")
                logger.info(f"     Size: {len(content):,} characters")
                
                step_time = time.time() - step_start
                self.metrics['step_times']['pdf_to_markdown'] = step_time
                
                return True
            else:
                logger.error("Markdown file not generated")
                return False
                
        except Exception as e:
            logger.error(f"PDF parsing failed: {e}")
            return False
    
    def run_chunking_pipeline(self) -> bool:
        """
        Pipeline 2: Markdown → Chunks
        Run chunking strategy
        """
        if self.state['chunks_created']:
            logger.info("Chunks already created, skipping...")
            return True
        
        logger.info("=" * 80)
        logger.info("PIPELINE 2: MARKDOWN → CHUNKS")
        logger.info("=" * 80)
        
        step_start = time.time()
        
        try:
            # Load markdown
            markdown_file = Path(self.config['output_dir']) / 'fintbx_complete.md'
            if not markdown_file.exists():
                logger.error(f"Markdown file not found: {markdown_file}")
                return False
            
            with open(markdown_file, 'r', encoding='utf-8') as f:
                text = f.read()
            
            logger.info(f"Loaded markdown: {len(text):,} characters")
            
            # Select chunking strategy
            chunker_name = self.config.get('chunker', 'hybrid')
            logger.info(f"Using chunking strategy: {chunker_name}")
            
            # Import chunker
            if chunker_name == 'hybrid':
                from chunkers.hybrid_chunker import HybridChunker
                chunker = HybridChunker(
                    chunk_size=self.config.get('chunk_size', 1000),
                    chunk_overlap=self.config.get('chunk_overlap', 200)
                )
            elif chunker_name == 'recursive':
                from chunkers.base_chunker import RecursiveCharacterChunker
                chunker = RecursiveCharacterChunker(
                    chunk_size=self.config.get('chunk_size', 1000),
                    chunk_overlap=self.config.get('chunk_overlap', 200)
                )
            elif chunker_name == 'markdown':
                from chunkers.base_chunker import MarkdownHeaderChunker
                chunker = MarkdownHeaderChunker(
                    chunk_size=self.config.get('chunk_size', 1000),
                    chunk_overlap=self.config.get('chunk_overlap', 200)
                )
            elif chunker_name == 'code':
                from chunkers.base_chunker import CodeAwareChunker
                chunker = CodeAwareChunker(
                    chunk_size=self.config.get('chunk_size', 1000),
                    chunk_overlap=self.config.get('chunk_overlap', 200)
                )
            else:
                logger.error(f"Unknown chunking strategy: {chunker_name}")
                return False
            
            # Apply chunking
            metadata = {'source': 'fintbx.pdf'}
            chunks = chunker.chunk(text, metadata)
            
            # Save chunks
            chunks_file = Path(self.config['output_dir']) / 'chunks' / f'chunks_{chunker_name}.json'
            chunks_file.parent.mkdir(parents=True, exist_ok=True)
            
            with open(chunks_file, 'w', encoding='utf-8') as f:
                json.dump([chunk.to_dict() for chunk in chunks], f, indent=2, ensure_ascii=False)
            
            self.metrics['chunks_created'] = len(chunks)
            self.state['chunks_created'] = True
            self.save_checkpoint()
            
            logger.info(f"[OK] Created {len(chunks)} chunks")
            logger.info(f"     Saved to: {chunks_file}")
            
            step_time = time.time() - step_start
            self.metrics['step_times']['chunking'] = step_time
            
            return True
            
        except Exception as e:
            logger.error(f"Chunking failed: {e}")
            import traceback
            logger.error(traceback.format_exc())
            return False
    
    def run_embedding_pipeline(self) -> bool:
        """
        Pipeline 3: Chunks → Embeddings
        Generate embeddings for chunks
        """
        if self.state['embeddings_generated']:
            logger.info("Embeddings already generated, skipping...")
            return True
        
        logger.info("=" * 80)
        logger.info("PIPELINE 3: CHUNKS → EMBEDDINGS")
        logger.info("=" * 80)
        
        step_start = time.time()
        
        try:
            # Load chunks
            chunker_name = self.config.get('chunker', 'hybrid')
            chunks_file = Path(self.config['output_dir']) / 'chunks' / f'chunks_{chunker_name}.json'
            
            if not chunks_file.exists():
                logger.error(f"Chunks file not found: {chunks_file}")
                return False
            
            with open(chunks_file, 'r', encoding='utf-8') as f:
                chunks_data = json.load(f)
            
            # Convert to Chunk objects
            chunks = []
            for item in chunks_data:
                chunk = Chunk(
                    content=item['content'],
                    metadata=item['metadata'],
                    embeddings=item.get('embeddings')
                )
                chunks.append(chunk)
            
            logger.info(f"Loaded {len(chunks)} chunks")
            
            # Generate embeddings
            embedder = Embedder(
                model=self.config.get('embedding_model', 'text-embedding-3-large'),
                dimension=self.config.get('embedding_dimension', 3072),
                batch_size=self.config.get('embedding_batch_size', 100)
            )
            
            logger.info("Generating embeddings...")
            embedded_chunks = embedder.embed_chunks(chunks, show_progress=True)
            
            # Save embedded chunks
            embedded_file = Path(self.config['output_dir']) / 'chunks' / f'chunks_{chunker_name}_embedded.json'
            with open(embedded_file, 'w', encoding='utf-8') as f:
                json.dump([chunk.to_dict() for chunk in embedded_chunks], f, indent=2, ensure_ascii=False)
            
            # Update metrics
            stats = embedder.get_stats()
            self.metrics['embeddings_generated'] = stats['embedded_chunks']
            self.metrics['total_tokens'] = stats['total_tokens']
            self.metrics['total_cost'] = stats['total_cost']
            
            self.state['embeddings_generated'] = True
            self.save_checkpoint()
            
            logger.info(f"[OK] Generated embeddings for {stats['embedded_chunks']} chunks")
            logger.info(f"     Total tokens: {stats['total_tokens']:,}")
            logger.info(f"     Total cost: ${stats['total_cost']:.4f}")
            logger.info(f"     Saved to: {embedded_file}")
            
            step_time = time.time() - step_start
            self.metrics['step_times']['embedding'] = step_time
            
            return True
            
        except Exception as e:
            logger.error(f"Embedding generation failed: {e}")
            import traceback
            logger.error(traceback.format_exc())
            return False
    
    def run_storage_pipeline(self) -> bool:
        """
        Pipeline 4: Embeddings → Vector Storage
        Store embeddings in Pinecone
        """
        if self.state['vectors_stored']:
            logger.info("Vectors already stored, skipping...")
            return True
        
        logger.info("=" * 80)
        logger.info("PIPELINE 4: EMBEDDINGS → VECTOR STORAGE")
        logger.info("=" * 80)
        
        step_start = time.time()
        
        try:
            # Load embedded chunks
            chunker_name = self.config.get('chunker', 'hybrid')
            embedded_file = Path(self.config['output_dir']) / 'chunks' / f'chunks_{chunker_name}_embedded.json'
            
            if not embedded_file.exists():
                logger.error(f"Embedded chunks file not found: {embedded_file}")
                return False
            
            with open(embedded_file, 'r', encoding='utf-8') as f:
                chunks_data = json.load(f)
            
            # Convert to Chunk objects
            chunks = []
            for item in chunks_data:
                chunk = Chunk(
                    content=item['content'],
                    metadata=item['metadata'],
                    embeddings=item.get('embeddings')
                )
                chunks.append(chunk)
            
            logger.info(f"Loaded {len(chunks)} embedded chunks")
            
            # Initialize Pinecone store
            store = PineconeStore(
                index_name=self.config.get('index_name', 'fintbx-embeddings'),
                dimension=self.config.get('embedding_dimension', 3072),
                metric=self.config.get('metric', 'cosine'),
                cloud=self.config.get('cloud', 'aws'),
                region=self.config.get('region', 'us-east-1'),
                batch_size=self.config.get('storage_batch_size', 100)
            )
            
            # Create/connect to index
            logger.info("Creating/connecting to Pinecone index...")
            try:
                store.create_index(force=False)
            except Exception as e:
                logger.info("Index already exists, connecting...")
                store.connect_index()
            
            # Upload chunks
            logger.info("Uploading chunks to Pinecone...")
            upserted = store.upsert_chunks(chunks, namespace=None, show_progress=True)
            
            # Update metrics
            self.metrics['vectors_stored'] = upserted
            self.state['vectors_stored'] = True
            self.save_checkpoint()
            
            # Get stats
            storage_stats = store.get_stats()
            index_stats = store.get_index_stats()
            
            logger.info(f"[OK] Uploaded {upserted} vectors to Pinecone")
            logger.info(f"     Index: {self.config.get('index_name', 'fintbx-embeddings')}")
            logger.info(f"     Total vectors in index: {index_stats.get('total_vector_count', 'N/A')}")
            
            step_time = time.time() - step_start
            self.metrics['step_times']['storage'] = step_time
            
            return True
            
        except Exception as e:
            logger.error(f"Storage failed: {e}")
            import traceback
            logger.error(traceback.format_exc())
            return False
    
    def run(self, dry_run: bool = False, pipeline: str = 'all') -> bool:
        """
        Run pipeline
        
        Args:
            dry_run: If True, validate configuration without running
            pipeline: Which pipeline to run ('1', '2', or 'all')
            
        Returns:
            True if successful
        """
        logger.info("=" * 80)
        logger.info("AURELIA PIPELINE ORCHESTRATOR")
        logger.info("=" * 80)
        logger.info(f"Configuration:")
        logger.info(f"  PDF File: {self.config.get('pdf_file', 'N/A')}")
        logger.info(f"  Output Dir: {self.config.get('output_dir', 'N/A')}")
        logger.info(f"  Chunker: {self.config.get('chunker', 'hybrid')}")
        logger.info(f"  Embedding Model: {self.config.get('embedding_model', 'text-embedding-3-large')}")
        logger.info(f"  Index Name: {self.config.get('index_name', 'fintbx-embeddings')}")
        logger.info(f"  Resume: {self.config.get('resume', False)}")
        logger.info(f"  Dry Run: {dry_run}")
        logger.info(f"  Pipeline: {pipeline}")
        logger.info("=" * 80)
        
        if dry_run:
            logger.info("DRY RUN: Validating configuration...")
            return self.validate_config(pipeline)
        
        # Determine which steps to run
        if pipeline == '1':
            # Pipeline 1: PDF → Markdown
            logger.info("\n" + "=" * 80)
            logger.info("RUNNING PIPELINE 1: PDF → MARKDOWN")
            logger.info("=" * 80)
            steps = [("PDF → Markdown", self.run_pdf_parser)]
        elif pipeline == '2':
            # Pipeline 2: Markdown → Chunks → Embeddings → Storage
            logger.info("\n" + "=" * 80)
            logger.info("RUNNING PIPELINE 2: MARKDOWN → CHUNKS → EMBEDDINGS → STORAGE")
            logger.info("=" * 80)
            steps = [
                ("Markdown → Chunks", self.run_chunking_pipeline),
                ("Chunks → Embeddings", self.run_embedding_pipeline),
                ("Embeddings → Storage", self.run_storage_pipeline)
            ]
        else:
            # Run all steps
            logger.info("\n" + "=" * 80)
            logger.info("RUNNING COMPLETE PIPELINE")
            logger.info("=" * 80)
            steps = [
                ("PDF → Markdown", self.run_pdf_parser),
                ("Markdown → Chunks", self.run_chunking_pipeline),
                ("Chunks → Embeddings", self.run_embedding_pipeline),
                ("Embeddings → Storage", self.run_storage_pipeline)
            ]
        
        for step_name, step_func in steps:
            logger.info(f"\nRunning step: {step_name}")
            if not step_func():
                logger.error(f"Pipeline failed at step: {step_name}")
                return False
        
        # Pipeline complete
        self.metrics['pipeline_time'] = time.time() - self.start_time
        self.save_metrics()
        
        logger.info("\n" + "=" * 80)
        logger.info("PIPELINE COMPLETE!")
        logger.info("=" * 80)
        self.print_summary()
        
        return True
    
    def validate_config(self, pipeline: str = 'all') -> bool:
        """Validate pipeline configuration"""
        logger.info("Validating configuration...")
        
        # Check PDF file (only needed for pipeline 1 or all)
        if pipeline in ['1', 'all']:
            if self.config.get('pdf_file'):
                pdf_file = Path(self.config['pdf_file'])
                if not pdf_file.exists():
                    logger.error(f"PDF file not found: {pdf_file}")
                    return False
                logger.info(f"✓ PDF file exists: {pdf_file}")
        
        # Check markdown file (only needed for pipeline 2)
        if pipeline == '2':
            markdown_file = Path(self.config.get('output_dir', 'data/parsed')) / 'fintbx_complete.md'
            if not markdown_file.exists():
                logger.error(f"Markdown file not found: {markdown_file}")
                logger.error("Please run Pipeline 1 first to generate markdown")
                return False
            logger.info(f"✓ Markdown file exists: {markdown_file}")
        
        # Check API keys (only needed for pipeline 2 or all)
        if pipeline in ['2', 'all']:
            if not os.getenv('OPENAI_API_KEY'):
                logger.error("OPENAI_API_KEY not set")
                return False
            logger.info("✓ OPENAI_API_KEY is set")
            
            if not os.getenv('PINECONE_API_KEY'):
                logger.error("PINECONE_API_KEY not set")
                return False
            logger.info("✓ PINECONE_API_KEY is set")
        
        # Check output directory
        output_dir = Path(self.config.get('output_dir', 'data/parsed'))
        output_dir.mkdir(parents=True, exist_ok=True)
        logger.info(f"✓ Output directory ready: {output_dir}")
        
        logger.info("\n✓ Configuration validated successfully!")
        return True
    
    def save_metrics(self):
        """Save pipeline metrics to file"""
        metrics_file = Path(self.config['output_dir']) / 'pipeline_metrics.json'
        
        with open(metrics_file, 'w', encoding='utf-8') as f:
            json.dump({
                'timestamp': datetime.now().isoformat(),
                'config': self.config,
                'metrics': self.metrics,
                'state': self.state
            }, f, indent=2)
        
        logger.info(f"Metrics saved to: {metrics_file}")
    
    def print_summary(self):
        """Print pipeline summary"""
        logger.info("\n" + "=" * 80)
        logger.info("PIPELINE SUMMARY")
        logger.info("=" * 80)
        logger.info(f"Markdown Size: {self.metrics['markdown_size']:,} characters")
        logger.info(f"Chunks Created: {self.metrics['chunks_created']}")
        logger.info(f"Embeddings Generated: {self.metrics['embeddings_generated']}")
        logger.info(f"Vectors Stored: {self.metrics['vectors_stored']}")
        logger.info(f"Total Tokens: {self.metrics['total_tokens']:,}")
        logger.info(f"Total Cost: ${self.metrics['total_cost']:.4f}")
        logger.info(f"Pipeline Time: {self.metrics['pipeline_time']:.2f}s")
        
        logger.info("\nStep Times:")
        for step, step_time in self.metrics['step_times'].items():
            logger.info(f"  {step}: {step_time:.2f}s")
        
        logger.info("=" * 80)


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description="AURELIA Pipeline Orchestrator - Complete PDF to Vector Database Pipeline"
    )
    
    # Input/Output
    parser.add_argument('--pdf', type=str, default='data/raw/fintbx.pdf',
                       help='Path to PDF file')
    parser.add_argument('--output-dir', type=str, default='data/parsed',
                       help='Output directory for parsed data')
    
    # Chunking
    parser.add_argument('--chunker', type=str, default='hybrid',
                       choices=['hybrid', 'recursive', 'markdown', 'code'],
                       help='Chunking strategy to use')
    parser.add_argument('--chunk-size', type=int, default=1000,
                       help='Chunk size in characters')
    parser.add_argument('--chunk-overlap', type=int, default=200,
                       help='Chunk overlap in characters')
    
    # Embeddings
    parser.add_argument('--embedding-model', type=str, default='text-embedding-3-large',
                       help='Embedding model to use')
    parser.add_argument('--embedding-dimension', type=int, default=3072,
                       help='Embedding dimension')
    parser.add_argument('--embedding-batch-size', type=int, default=100,
                       help='Batch size for embeddings')
    
    # Storage
    parser.add_argument('--index-name', type=str, default='fintbx-embeddings',
                       help='Pinecone index name')
    parser.add_argument('--metric', type=str, default='cosine',
                       choices=['cosine', 'euclidean', 'dotproduct'],
                       help='Distance metric')
    parser.add_argument('--cloud', type=str, default='aws',
                       choices=['aws', 'gcp', 'azure'],
                       help='Cloud provider')
    parser.add_argument('--region', type=str, default='us-east-1',
                       help='Cloud region')
    parser.add_argument('--storage-batch-size', type=int, default=100,
                       help='Batch size for storage')
    
    # Pipeline control
    parser.add_argument('--resume', action='store_true',
                       help='Resume from last checkpoint')
    parser.add_argument('--dry-run', action='store_true',
                       help='Validate configuration without running')
    parser.add_argument('--pipeline', type=str, default='all',
                       choices=['1', '2', 'all'],
                       help='Which pipeline to run: 1 (PDF→Markdown), 2 (Markdown→Storage), all (complete)')
    
    args = parser.parse_args()
    
    # Build configuration
    config = {
        'pdf_file': args.pdf,
        'output_dir': args.output_dir,
        'chunker': args.chunker,
        'chunk_size': args.chunk_size,
        'chunk_overlap': args.chunk_overlap,
        'embedding_model': args.embedding_model,
        'embedding_dimension': args.embedding_dimension,
        'embedding_batch_size': args.embedding_batch_size,
        'index_name': args.index_name,
        'metric': args.metric,
        'cloud': args.cloud,
        'region': args.region,
        'storage_batch_size': args.storage_batch_size,
        'resume': args.resume
    }
    
    # Run pipeline
    orchestrator = PipelineOrchestrator(config)
    success = orchestrator.run(dry_run=args.dry_run, pipeline=args.pipeline)
    
    sys.exit(0 if success else 1)


if __name__ == '__main__':
    main()


import tempfile
import unittest
from pathlib import Path

from memograph import MemoryKernel, MemoryType


class KernelTests(unittest.TestCase):
    def test_remember_ingest_and_context_window(self):
        with tempfile.TemporaryDirectory() as tmp:
            kernel = MemoryKernel(tmp)

            created = kernel.remember(
                title="Team Sync",
                content="Decided to use BFS graph traversal for retrieval.",
                memory_type=MemoryType.EPISODIC,
                tags=["#design", "retrieval"],
            )
            self.assertTrue(Path(created).exists())

            stats = kernel.ingest()
            self.assertEqual(stats["total"], 1)

            context = kernel.context_window(
                query="how does retrieval work",
                tags=["retrieval"],
                depth=2,
                top_k=4,
                token_limit=256,
            )
            self.assertIn("Team Sync", context)
            self.assertIn("BFS graph traversal", context)

    def test_remember_generates_unique_filenames(self):
        with tempfile.TemporaryDirectory() as tmp:
            kernel = MemoryKernel(tmp)

            first = kernel.remember("Same Title", "one", tags=["a"])
            second = kernel.remember("Same Title", "two", tags=["b"])

            self.assertNotEqual(first, second)
            self.assertTrue(Path(first).exists())
            self.assertTrue(Path(second).exists())


class GAMKernelTests(unittest.TestCase):
    """Test MemoryKernel with GAM enabled."""

    def test_kernel_with_gam_enabled(self):
        """Test kernel initialization with GAM."""
        with tempfile.TemporaryDirectory() as tmp:
            kernel = MemoryKernel(tmp, use_gam=True)

            # Create and ingest memories
            kernel.remember(
                title="Python Tutorial",
                content="Learn Python programming basics",
                memory_type=MemoryType.SEMANTIC,
                tags=["python"],
                salience=0.8,
            )

            kernel.remember(
                title="Python Functions",
                content="Functions in Python use def keyword",
                memory_type=MemoryType.SEMANTIC,
                tags=["python"],
                salience=0.7,
            )

            stats = kernel.ingest()
            self.assertEqual(stats["total"], 2)

            # Test retrieval with GAM
            nodes = kernel.retrieve_nodes("python", top_k=5)
            self.assertGreater(len(nodes), 0)

    def test_kernel_explain_retrieval(self):
        """Test explain_retrieval with GAM."""
        with tempfile.TemporaryDirectory() as tmp:
            kernel = MemoryKernel(tmp, use_gam=True)

            kernel.remember(
                title="Test Memory",
                content="Test content for GAM",
                memory_type=MemoryType.FACT,
                salience=0.9,
            )

            kernel.ingest()

            # Test explain_retrieval
            explanation = kernel.explain_retrieval("test", top_k=3)

            self.assertIn("query", explanation)
            self.assertIn("results", explanation)
            self.assertIn("candidates_found", explanation)

    def test_kernel_gam_statistics(self):
        """Test get_gam_statistics with GAM."""
        with tempfile.TemporaryDirectory() as tmp:
            kernel = MemoryKernel(tmp, use_gam=True)

            kernel.remember(title="Memory 1", content="Content 1", memory_type=MemoryType.FACT)

            kernel.ingest()

            # Perform some retrievals
            kernel.retrieve_nodes("content", top_k=3)
            kernel.retrieve_nodes("memory", top_k=3)

            # Test GAM statistics
            stats = kernel.get_gam_statistics()

            self.assertIn("total_queries", stats)
            self.assertGreaterEqual(stats["total_queries"], 2)


if __name__ == "__main__":
    unittest.main()

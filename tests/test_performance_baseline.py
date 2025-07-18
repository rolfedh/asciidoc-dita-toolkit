#!/usr/bin/env python3
"""
Performance baseline test to compare legacy vs ADTModule plugin execution.

This test ensures no performance regression when migrating from legacy to ADTModule pattern.
"""

import time
import tempfile
import os
import sys
from pathlib import Path
from typing import Dict, List, Tuple
import statistics
import pytest

# Add necessary paths
workspace_root = Path(__file__).parent.parent  # Go up from tests/ to project root
src_path = workspace_root / "src"
sys.path.insert(0, str(src_path))
sys.path.insert(0, str(workspace_root))

def create_test_files(num_files: int = 10, entities_per_file: int = 20) -> List[str]:
    """Create test .adoc files with entity references for performance testing."""
    import random
    random.seed(42)  # Set a fixed seed for deterministic behavior
    
    test_files = []
    
    # Sample content with various entities
    entities = [
        "&copy;", "&trade;", "&reg;", "&mdash;", "&ndash;", 
        "&ldquo;", "&rdquo;", "&lsquo;", "&rsquo;", "&hellip;",
        "&bull;", "&deg;", "&para;", "&sect;", "&middot;"
    ]
    
    for i in range(num_files):
        with tempfile.NamedTemporaryFile(mode='w', suffix='.adoc', delete=False) as f:
            f.write(f"= Test Document {i+1}\n\n")
            f.write("This is a test document for performance testing.\n\n")
            
            for j in range(entities_per_file):
                entity = entities[j % len(entities)]
                f.write(f"Line {j+1}: This text contains {entity} entity reference.\n")
            
            f.write("\n// This is a comment with &copy; entity that should be ignored\n")
            f.write("////\n")
            f.write("Block comment with &trade; entity that should be ignored\n")
            f.write("////\n")
            
            test_files.append(f.name)
    
    return test_files

@pytest.fixture(scope="function")
def test_files():
    """Pytest fixture to create test files for performance testing."""
    files = create_test_files(num_files=5, entities_per_file=10)  # Smaller for faster tests
    yield files
    # Cleanup after test
    for file_path in files:
        try:
            os.unlink(file_path)
        except (OSError, FileNotFoundError):
            pass

def cleanup_test_files(test_files: List[str]) -> None:
    """Clean up test files."""
    for file_path in test_files:
        try:
            os.unlink(file_path)
        except OSError:
            pass

def measure_execution_time(func, *args, **kwargs) -> Tuple[float, any]:
    """Measure execution time of a function."""
    start_time = time.perf_counter()
    result = func(*args, **kwargs)
    end_time = time.perf_counter()
    return end_time - start_time, result

def test_legacy_performance(test_files) -> None:
    """Test legacy plugin performance."""
    try:
        from asciidoc_dita_toolkit.asciidoc_dita.plugins.EntityReference import main
        
        # Create mock args
        class MockArgs:
            def __init__(self, files):
                self.file = None
                self.recursive = False
                self.directory = "."
                self.verbose = False
                self.silent = True  # Reduce output during testing
                self.files = files
        
        # Backup original files (copy them to restore later)
        backup_files = {}
        for file_path in test_files:
            with open(file_path, 'r') as f:
                backup_files[file_path] = f.read()
        
        # Measure legacy performance
        times = []
        for i in range(5):  # Run 5 times for better statistical relevance
            # Restore files to original state
            for file_path, content in backup_files.items():
                with open(file_path, 'w') as f:
                    f.write(content)
            
            # Force legacy mode by temporarily disabling ADTModule
            import asciidoc_dita_toolkit.asciidoc_dita.plugins.EntityReference as er_module
            original_available = er_module.ADT_MODULE_AVAILABLE
            er_module.ADT_MODULE_AVAILABLE = False
            
            try:
                # Process each file individually
                execution_time = 0
                for file_path in test_files:
                    args = MockArgs([file_path])
                    args.file = file_path
                    
                    time_taken, _ = measure_execution_time(main, args)
                    execution_time += time_taken
                
                times.append(execution_time)
                
            finally:
                # Restore ADTModule availability
                er_module.ADT_MODULE_AVAILABLE = original_available
        
        stats = {
            "mean": statistics.mean(times),
            "median": statistics.median(times),
            "stdev": statistics.stdev(times) if len(times) > 1 else 0,
            "min": min(times),
            "max": max(times),
            "times": times
        }
        
        # Basic performance assertions
        assert stats["mean"] > 0, "Legacy performance test should take some time"
        assert stats["mean"] < 10.0, "Legacy performance should complete within 10 seconds"
        assert len(stats["times"]) == 5, "Should have 5 performance measurements"
        
    except Exception as e:
        pytest.fail(f"Error testing legacy performance: {e}")

def test_adtmodule_performance(test_files) -> None:
    """Test ADTModule plugin performance."""
    try:
        from asciidoc_dita_toolkit.asciidoc_dita.plugins.EntityReference import EntityReferenceModule
        
        # Backup original files
        backup_files = {}
        for file_path in test_files:
            with open(file_path, 'r') as f:
                backup_files[file_path] = f.read()
        
        # Measure ADTModule performance
        times = []
        for i in range(5):  # Run 5 times for better statistical relevance
            # Restore files to original state
            for file_path, content in backup_files.items():
                with open(file_path, 'w') as f:
                    f.write(content)
            
            # Create and initialize module
            module = EntityReferenceModule()
            config = {
                "verbose": False,
                "timeout_seconds": 30,
                "cache_size": 1000,
                "skip_comments": True
            }
            module.initialize(config)
            
            # Process each file individually
            execution_time = 0
            for file_path in test_files:
                context = {
                    "file": file_path,
                    "recursive": False,
                    "directory": str(Path(file_path).parent),
                    "verbose": False
                }
                
                time_taken, _ = measure_execution_time(module.execute, context)
                execution_time += time_taken
            
            # Cleanup
            module.cleanup()
            times.append(execution_time)
        
        stats = {
            "mean": statistics.mean(times),
            "median": statistics.median(times),
            "stdev": statistics.stdev(times) if len(times) > 1 else 0,
            "min": min(times),
            "max": max(times),
            "times": times
        }
        
        # Basic performance assertions
        assert stats["mean"] > 0, "ADTModule performance test should take some time"
        assert stats["mean"] < 10.0, "ADTModule performance should complete within 10 seconds"
        assert len(stats["times"]) == 5, "Should have 5 performance measurements"
        
    except Exception as e:
        pytest.fail(f"Error testing ADTModule performance: {e}")

def calculate_performance_metrics(legacy_stats: Dict, adtmodule_stats: Dict) -> Dict:
    """Calculate performance comparison metrics."""
    if "error" in legacy_stats or "error" in adtmodule_stats:
        return {"error": "Could not calculate metrics due to errors"}
    
    legacy_mean = legacy_stats["mean"]
    adtmodule_mean = adtmodule_stats["mean"]
    
    # Calculate percentage difference
    if legacy_mean > 0:
        percentage_diff = ((adtmodule_mean - legacy_mean) / legacy_mean) * 100
    else:
        percentage_diff = 0
    
    # Determine performance verdict
    if percentage_diff < -5:
        verdict = "🚀 IMPROVEMENT"
    elif percentage_diff > 10:
        verdict = "⚠️ REGRESSION"
    else:
        verdict = "✅ EQUIVALENT"
    
    return {
        "legacy_mean": legacy_mean,
        "adtmodule_mean": adtmodule_mean,
        "percentage_diff": percentage_diff,
        "verdict": verdict,
        "is_regression": percentage_diff > 10
    }

def main():
    """Run performance baseline tests."""
    print("🚀 ADTModule Performance Baseline Test")
    print("=" * 50)
    
    # Test configuration
    num_files = 10
    entities_per_file = 20
    
    print(f"Creating {num_files} test files with {entities_per_file} entities each...")
    test_files = create_test_files(num_files, entities_per_file)
    
    try:
        print(f"Created {len(test_files)} test files")
        
        # Test legacy performance
        print("\n📊 Testing Legacy Plugin Performance...")
        legacy_stats = test_legacy_performance(test_files)
        
        if "error" not in legacy_stats:
            print(f"   Mean execution time: {legacy_stats['mean']:.4f}s")
            print(f"   Median execution time: {legacy_stats['median']:.4f}s")
            print(f"   Standard deviation: {legacy_stats['stdev']:.4f}s")
            print(f"   Min/Max: {legacy_stats['min']:.4f}s / {legacy_stats['max']:.4f}s")
        else:
            print(f"   Error: {legacy_stats['error']}")
        
        # Test ADTModule performance
        print("\n📊 Testing ADTModule Plugin Performance...")
        adtmodule_stats = test_adtmodule_performance(test_files)
        
        if "error" not in adtmodule_stats:
            print(f"   Mean execution time: {adtmodule_stats['mean']:.4f}s")
            print(f"   Median execution time: {adtmodule_stats['median']:.4f}s")
            print(f"   Standard deviation: {adtmodule_stats['stdev']:.4f}s")
            print(f"   Min/Max: {adtmodule_stats['min']:.4f}s / {adtmodule_stats['max']:.4f}s")
        else:
            print(f"   Error: {adtmodule_stats['error']}")
        
        # Calculate comparison metrics
        print("\n📈 Performance Comparison:")
        print("-" * 30)
        
        metrics = calculate_performance_metrics(legacy_stats, adtmodule_stats)
        
        if "error" not in metrics:
            print(f"   Legacy mean time: {metrics['legacy_mean']:.4f}s")
            print(f"   ADTModule mean time: {metrics['adtmodule_mean']:.4f}s")
            print(f"   Performance difference: {metrics['percentage_diff']:+.1f}%")
            print(f"   Verdict: {metrics['verdict']}")
            
            if metrics['is_regression']:
                print("\n⚠️  WARNING: Performance regression detected!")
                print("   Consider optimizing ADTModule implementation.")
                return False
            else:
                print("\n✅ Performance baseline validation: PASSED")
                return True
        else:
            print(f"   Error: {metrics['error']}")
            return False
            
    finally:
        # Cleanup
        print(f"\n🧹 Cleaning up {len(test_files)} test files...")
        cleanup_test_files(test_files)

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)

import moviepy
import sys
print(f"MoviePy version: {moviepy.__version__}")
print(f"MoviePy file: {moviepy.__file__}")

try:
    import moviepy.editor
    print("SUCCESS: moviepy.editor found")
except ImportError as e:
    print(f"FAILURE: {e}")

# check what is available in moviepy
print("Attributes in moviepy:")
print(dir(moviepy))

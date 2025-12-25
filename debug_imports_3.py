import moviepy
try:
    from moviepy import concatenate_videoclips
    print(f"Start: {concatenate_videoclips}")
except ImportError:
    print("Top level failed")

import pkgutil
print("Submodules:")
for importer, modname, ispkg in pkgutil.walk_packages(moviepy.__path__, moviepy.__name__ + "."):
    if "concatenate" in modname:
        print(modname)

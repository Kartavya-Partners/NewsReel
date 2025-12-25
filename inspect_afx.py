
try:
    from moviepy import afx
    print("Imported 'from moviepy import afx'")
    print(dir(afx))
except ImportError:
    print("Could not import 'from moviepy import afx'. Trying submodule...")
    try:
        import moviepy.audio.fx.all as afx
        print("Imported 'import moviepy.audio.fx.all as afx'")
        print(dir(afx))
    except Exception as e:
        print(e)

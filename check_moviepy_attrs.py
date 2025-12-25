from moviepy import ColorClip, vfx
c = ColorClip(size=(100,100), color=(0,0,0))
print("with_opacity:", hasattr(c, 'with_opacity'))
print("set_opacity:", hasattr(c, 'set_opacity'))
print("vfx.Opacity:", hasattr(vfx, 'Opacity'))
print("vfx.opacity:", hasattr(vfx, 'opacity'))
print("with_effects:", hasattr(c, 'with_effects'))
print("resized:", hasattr(c, 'resized'))
print("resize:", hasattr(c, 'resize'))
print("with_position:", hasattr(c, 'with_position'))
print("vfx.FadeIn:", hasattr(vfx, 'FadeIn'))
print("vfx.fadein:", hasattr(vfx, 'fadein'))
import moviepy.video.fx.all as vfx_all
import moviepy.video.io.VideoFileClip
# Mock or check plain VideoClip if VideoFileClip needs a file
from moviepy import VideoClip
vc = VideoClip(lambda t: np.zeros((100,100,3)), duration=1)
print("with_audio:", hasattr(vc, 'with_audio'))
print("set_audio:", hasattr(vc, 'set_audio'))

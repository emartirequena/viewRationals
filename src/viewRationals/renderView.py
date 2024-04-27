import gc
import numpy as np
import moderngl as mgl
from copy import deepcopy
from madcad import rendering, uvec2, fmat4
from utils import collect


class RenderView(rendering.Offscreen):
    def __init__(self, scene, size=uvec2(1920, 1080), navigation=None, projection=None, share=True, ctx=None):
        self.scene: rendering.Scene = scene
        self.projection = projection
        self.navigation = navigation

        self.uniforms = {'proj':fmat4(1), 'view':fmat4(1), 'projview':fmat4(1)}	# last frame rendering constants
        self.targets = []
        self.steps = []
        self.step = 0
        self.stepi = 0

        # dump targets
        self.map_depth = None
        self.map_idents = None
        self.fresh = set()	# set of refreshed internal variables since the last render

        if not ctx:
            self.scene.ctx = mgl.create_standalone_context(share=share)
        else:
            self.scene.ctx = ctx

        self.init(size)
        self.preload()

    def __del__(self):
        del self.scene
        del self.uniforms
        del self.targets
        del self.steps
        del self.map_depth
        del self.map_idents
        del self.projection
        del self.navigation
        gc.collect()

    def init(self, size):
        w, h = size

        ctx = self.scene.ctx
        assert ctx, 'context is not initialized'

        # self.fb_frame is already created and sized by Qt
        self.fb_screen = ctx.simple_framebuffer(size)
        self.fb_ident = ctx.simple_framebuffer(size, components=3, dtype='f1')
        self.targets = [ ('screen', self.fb_screen, self.setup_screen),
                            ('ident', self.fb_ident, self.setup_ident)]
        self.map_ident = np.empty((h,w), dtype='u2')
        self.map_depth = np.empty((h,w), dtype='f4')

    def set_projection(self, projection):
        self.projection = deepcopy(projection)

    def set_navigation(self, navigation):
        self.navigation = deepcopy(navigation)

    def resize(self, size):
        if size != self.fb_screen.size:
            self.init(size)

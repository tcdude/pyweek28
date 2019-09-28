"""
Root class for all subclasses.
"""

__copyright__ = """
MIT License

Copyright (c) 2019 tcdude

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
"""
import builtins

# noinspection PyPackageRequirements
from direct.showbase.ShowBase import ShowBase
from panda3d import core


# noinspection PyArgumentList
class GameData(ShowBase):
    def __init__(self):
        if not hasattr(builtins, 'base'):
            # noinspection PyCallByClass,PyArgumentList
            self.settings = core.load_prc_file(
                core.Filename.expand_from('$MAIN_DIR/settings.prc')
            )
            ShowBase.__init__(self)
            # noinspection PyArgumentList
            self.global_clock = core.ClockObject.get_global_clock()
            self.keyboard_map = self.win.get_keyboard_map()
            # onscreen hint text
            self.__hints = self.aspect2d.attach_new_node('hints')
            self.__hints.set_transparency(core.TransparencyAttrib.M_alpha)
            self.__hints.set_alpha_scale(0.6)
            self.__hint_active = False
            self.__hint_queue = []
            self.__last_msg = None
            self.task_mgr.add(self.__update)
        self.no_movement = True

    def __update(self, task):
        if self.__hint_queue and not self.__hint_active:
            self.__display_next_hint()
        return task.cont

    def display_hint(self, msg, duration=4, only_inactive=False):
        if only_inactive and self.__hint_active:
            return
        self.__hint_queue.append((msg, duration))

    def __display_next_hint(self):
        if not self.__hint_queue:
            return
        self.__hint_active = True
        msg, duration = self.__hint_queue.pop(0)
        if msg == self.__last_msg:
            self.__hints.show()
        else:
            self.__hints.show()
            self.__hints.get_children().detach()
            self.__last_msg = msg
            tn = core.TextNode('hint')
            tnp = self.__hints.attach_new_node(tn)
            tn.set_text(msg)
            tnp.set_scale(0.05)
            tnp.set_pos(
                -0.4,
                0,
                0.5
            )
        self.do_method_later(duration, self.__remove_hints, 'remove_hint')

    def __remove_hints(self, *_):
        self.__hints.hide()
        self.__hint_active = False

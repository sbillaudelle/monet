#! /usr/bin/env python
# -*- coding: utf-8 -*-

# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston,
# MA 02110-1301, USA.

import os
import math

import gobject
import gtk
import clutter
import cluttergtk

import cream

PATH = '/home/stein/Bilder/'

def rounded_rectangle(cr, x, y, w, h, r=20):

    if r >= h / 2.0:
        r = h / 2.0

    cr.arc(x + r, y + r, r, math.pi, -.5 * math.pi)
    cr.arc(x + w - r, y + r, r, -.5 * math.pi, 0 * math.pi)
    cr.arc(x + w - r, y + h - r, r, 0 * math.pi, .5 * math.pi)
    cr.arc(x + r, y + h - r, r, .5 * math.pi, math.pi)
    cr.close_path()


class Image(clutter.Texture):

    def __init__(self, path, load=False):

        clutter.Texture.__init__(self)

        self.path = path
        self.loaded = False
        self.aspect_ratio = 1

        self.set_position(0, 0)

        if load:
            self.load()


    def load(self, async=False):

        if self.loaded:
            return

        self.loaded = True

        if async:
            self.set_load_async(True)

        self.connect('load-finished', self.load_finished_cb)
        self.set_from_file(self.path)


    def load_finished_cb(self, *args):
        self.aspect_ratio = float(self.get_width()) / float(self.get_height())


    def get_aspect_ratio(self):
        return self.aspect_ratio


    def fade_in(self):

        self.animate(clutter.AnimationMode(clutter.LINEAR), 400, 'opacity', 255)
        return False


    def fade_out(self):

        self.animate(clutter.AnimationMode(clutter.LINEAR), 400, 'opacity', 0)
        return False


class ControlAreaBackground(clutter.CairoTexture):

    def __init__(self):

        clutter.CairoTexture.__init__(self, 184, 68)

        ctx = self.cairo_create()
        rounded_rectangle(ctx, 0, 0, 184, 68, 15)

        ctx.set_source_rgba(0, 0, 0, .8)
        ctx.fill()

        #ctx.set_line_width(1)
        #rounded_rectangle(ctx, .5, .5, 183, 67, 15)
        #ctx.set_source_rgba(1, 1, 1, .4)
        #ctx.stroke()


class ControlArea(clutter.Group):

    __gsignals__ = {
        'previous-image': (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE, ()),
        'next-image': (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE, ())
        }

    def __init__(self):

        clutter.Group.__init__(self)

        self.set_reactive(True)

        self.background = ControlAreaBackground()
        self.add(self.background)

        self.icon_previous = Image('previous.svg', load=True)
        self.icon_previous.set_size(48, 48)
        self.icon_previous.set_position(11, 11)
        self.add(self.icon_previous)

        self.icon_slideshow = Image('slideshow.svg', load=True)
        self.icon_slideshow.set_size(48, 48)
        self.icon_slideshow.set_position(69, 11)
        self.add(self.icon_slideshow)

        self.icon_next = Image('next.svg', load=True)
        self.icon_next.set_size(48, 48)
        self.icon_next.set_position(127, 11)
        self.add(self.icon_next)

        self.icon_previous.set_reactive(True)
        self.icon_previous.connect('button-press-event', lambda *args: self.emit('previous-image'))

        self.icon_next.set_reactive(True)
        self.icon_next.connect('button-press-event', lambda *args: self.emit('next-image'))


    def fade_in(self):

        self.animate(clutter.AnimationMode(clutter.LINEAR), 400, 'opacity', 255)
        return False


    def fade_out(self):

        self.animate(clutter.AnimationMode(clutter.LINEAR), 400, 'opacity', 0)
        return False


class ImageView(cluttergtk.Embed):

    def __init__(self):

        cluttergtk.Embed.__init__(self)

        self.timeouts = {
            'control-area-fade-out': None
            }

        self.connect('size-allocate', self.size_allocate_cb)

        self.realize()
        self.stage = self.get_stage()
        self.stage.set_color(clutter.color_from_string('black'))

        self.images = []
        for i in os.listdir(PATH):
            if i.endswith('.png') or i.endswith('.jpg'):
                self.images.append(Image(PATH + i))

        self.current_image = None

        self.show_image(0, animate=False)

        self.control_area = ControlArea()
        self.control_area.set_depth(1)
        self.control_area.connect('previous-image', lambda *args: self.show_image(max(self.current_image - 1, 0)))
        self.control_area.connect('next-image', lambda *args: self.show_image(min(self.current_image + 1, len(self.images) - 1)))
        self.control_area.connect('enter-event', self.control_area_enter_event_cb)
        self.control_area.connect('leave-event', self.control_area_enter_leave_cb)
        self.stage.add(self.control_area)

        self.control_area.set_opacity(0)

        self.stage.connect('motion-event', self.motion_event_cb)


    def load_image(self, img, async=False):
        self.images[img].load(async)


    def show_image(self, img, animate=True):

        self.load_image(img)
        self.load_image(img + 1, async=True)

        if img == self.current_image:
            return False

        if self.current_image != None:
            old_image = self.images[self.current_image]
        else:
            old_image = None

        self.current_image = img

        self.stage.add(self.images[self.current_image])

        if animate:
            self.images[self.current_image].set_opacity(0)
            self.images[self.current_image].fade_in()
            if old_image:
                old_image.fade_out()

        self.calculate_image_position(self.images[self.current_image])

        return False


    def motion_event_cb(self, stage, event):

        self.control_area.fade_in()
        if self.timeouts['control-area-fade-out']:
            gobject.source_remove(self.timeouts['control-area-fade-out'])
            self.timeouts['control-area-fade-out'] = None

        if self.timeouts['control-area-fade-out'] != False:
            self.timeouts['control-area-fade-out'] = gobject.timeout_add(2000, lambda: self.control_area.fade_out())


    def control_area_enter_event_cb(self, control_area, event):

        if self.timeouts['control-area-fade-out']:
            gobject.source_remove(self.timeouts['control-area-fade-out'])

        self.timeouts['control-area-fade-out'] = False


    def control_area_enter_leave_cb(self, control_area, event):
        self.timeouts['control-area-fade-out'] = gobject.timeout_add(2000, lambda: self.control_area.fade_out())


    def calculate_image_position(self, image):

        image_aspect_ratio = image.get_aspect_ratio()
        view_aspect_ratio = float(self.allocation.width) / float(self.allocation.height)

        if image_aspect_ratio >= view_aspect_ratio:
            image.set_size(self.allocation.width, self.allocation.width / image_aspect_ratio)
            image.set_position(0, (self.allocation.height - self.allocation.width / image_aspect_ratio) / 2)
        else:
            image.set_size(self.allocation.height * image_aspect_ratio, self.allocation.height)
            image.set_position((self.allocation.width - self.allocation.height * image_aspect_ratio) / 2, 0)


    def size_allocate_cb(self, source, allocation):

        self.stage.set_size(allocation.width, allocation.height)
        self.calculate_image_position(self.images[self.current_image])

        self.control_area.set_position((allocation.width - self.control_area.get_size()[0]) / 2, allocation.height - self.control_area.get_size()[1] - 30)


class Monet(cream.Module):

    def __init__(self):

        cream.Module.__init__(self)

        self.window = gtk.Window()

        self.view = ImageView()
        self.window.add(self.view)
        self.window.set_size_request(800, 480)
        self.window.show_all()

        self.window.connect('destroy', lambda *args: self.quit())


if __name__ == '__main__':
    monet = Monet()
    monet.main()

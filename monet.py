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

#PATH = '/home/stein/Bilder/'
PATH = '/'
ICON_SIZE = 32
ICON_SPACING = 5
CONTROL_BOX_MARGIN = 8

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

        self.fade(255)
        return False


    def fade_out(self):

        self.fade(0)
        return False


    def fade(self, opacity, duration=400):
        self.animate(clutter.AnimationMode(clutter.LINEAR), duration, 'opacity', opacity)


class StartScreen(clutter.Group):

    __gsignals__ = {
        'show-open-dialog': (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE, ())
        }

    def __init__(self):

        clutter.Group.__init__(self)

        self.set_reactive(True)
        self.connect('button-release-event', lambda *args: self.emit('show-open-dialog'))

        self.icon = Image('data/images/monet.svg')
        self.icon.load()

        self.label = clutter.Label()
        self.label.set_color(clutter.Color(255, 255, 255, 200))
        self.label.set_font_name('Sans 12')
        self.label.set_text("Click to open files...")

        self.add(self.icon)
        self.add(self.label)


    def set_size(self, width, height):

        clutter.Group.set_size(self, width, height)
        self.icon.set_position((width - self.icon.get_width()) / 2, (height - self.icon.get_height() - self.label.get_height() - 10) / 2)
        self.label.set_position((width - self.label.get_width()) / 2, (height - self.icon.get_height() - self.label.get_height() - 10) / 2 + self.icon.get_height() + 10)


    def fade_in(self):

        self.fade(255)
        return False


    def fade_out(self):

        self.fade(0)
        return False


    def fade(self, opacity, duration=400):
        self.animate(clutter.AnimationMode(clutter.LINEAR), duration, 'opacity', opacity)


class ControlAreaBackground(clutter.CairoTexture):

    def __init__(self):

        clutter.CairoTexture.__init__(self, 3*ICON_SIZE + 2*ICON_SPACING + 2*CONTROL_BOX_MARGIN, ICON_SIZE + 2*CONTROL_BOX_MARGIN)

        ctx = self.cairo_create()
        rounded_rectangle(ctx, 0, 0, 3*ICON_SIZE + 2*ICON_SPACING + 2*CONTROL_BOX_MARGIN, ICON_SIZE + 2*CONTROL_BOX_MARGIN, 10)

        ctx.set_source_rgba(0, 0, 0, .6)
        ctx.fill()

        ctx.set_line_width(1)
        rounded_rectangle(ctx, .5, .5, 3*ICON_SIZE + 2*ICON_SPACING + 2*CONTROL_BOX_MARGIN - 1, ICON_SIZE + 2*CONTROL_BOX_MARGIN - 1, 10)
        ctx.set_source_rgba(1, 1, 1, .2)
        ctx.stroke()


class ControlArea(clutter.Group):
    """ A class representing the small box containing the control buttons. """

    __gsignals__ = {
        'previous-image': (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE, ()),
        'next-image': (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE, ())
        }

    def __init__(self):

        clutter.Group.__init__(self)

        # Enable UI events...
        self.set_reactive(True)

        # Add the background:
        self.background = ControlAreaBackground()
        self.add(self.background)

        # Add the icons...
        self.icon_previous = Image('data/images/previous.svg', load=True)
        self.icon_previous.set_size(ICON_SIZE, ICON_SIZE)
        self.icon_previous.set_position(CONTROL_BOX_MARGIN, CONTROL_BOX_MARGIN)
        self.icon_previous.set_opacity(150)
        self.add(self.icon_previous)

        self.icon_slideshow = Image('data/images/slideshow.svg', load=True)
        self.icon_slideshow.set_size(ICON_SIZE, ICON_SIZE)
        self.icon_slideshow.set_position(CONTROL_BOX_MARGIN + ICON_SIZE + ICON_SPACING, CONTROL_BOX_MARGIN)
        self.icon_slideshow.set_opacity(150)
        self.add(self.icon_slideshow)

        self.icon_next = Image('data/images/next.svg', load=True)
        self.icon_next.set_size(ICON_SIZE, ICON_SIZE)
        self.icon_next.set_position(CONTROL_BOX_MARGIN + 2*ICON_SIZE + 2*ICON_SPACING, CONTROL_BOX_MARGIN)
        self.icon_next.set_opacity(150)
        self.add(self.icon_next)

        self.icon_previous.set_reactive(True)
        self.icon_previous.connect('button-press-event', lambda *args: self.emit('previous-image'))
        self.icon_previous.connect('enter-event', lambda *args: self.icon_previous.fade(255, duration=200))
        self.icon_previous.connect('leave-event', lambda *args: self.icon_previous.fade(150, duration=200))

        self.icon_next.set_reactive(True)
        self.icon_next.connect('button-press-event', lambda *args: self.emit('next-image'))
        self.icon_next.connect('enter-event', lambda *args: self.icon_next.fade(255, duration=200))
        self.icon_next.connect('leave-event', lambda *args: self.icon_next.fade(150, duration=200))


    def fade_in(self):
        """ Fade in the control area... """

        self.animate(clutter.AnimationMode(clutter.LINEAR), 400, 'opacity', 255)
        return False


    def fade_out(self):
        """ Fade out the control area... """

        self.animate(clutter.AnimationMode(clutter.LINEAR), 400, 'opacity', 0)
        return False


class ImageView(cluttergtk.Embed):
    """
    A subclass of cluttergtk.Embed managing the displayed images
    including animations, etc. and the basic interaction through
    the control area.
    """

    __gsignals__ = {
        'show-open-dialog': (gobject.SIGNAL_RUN_FIRST, gobject.TYPE_NONE, ())
        }

    def __init__(self):

        cluttergtk.Embed.__init__(self)

        self.timeouts = {
            'control-area-fade-out': None
            }

        # Control the size of the surface and the images...
        self.connect('size-allocate', self.size_allocate_cb)

        # Initialize...
        self.realize()
        self.stage = self.get_stage()
        self.stage.set_color(clutter.color_from_string('black'))

        # Add some images...
        # TODO: Implement file dialog!
        self.images = []
        self.animate_transition = True

        # Show the first image...
        self.current_image = None

        # Initialize the control area...
        self.control_area = ControlArea()

        # Keep it above the images:
        self.control_area.set_depth(1)

        # Connect to the events from the control area...
        self.control_area.connect('previous-image', lambda *args: self.show_image(max(self.current_image - 1, 0), animate=self.animate_transition))
        self.control_area.connect('next-image', lambda *args: self.show_image(min(self.current_image + 1, len(self.images) - 1), animate=self.animate_transition))
        self.control_area.connect('enter-event', self.control_area_enter_event_cb)
        self.control_area.connect('leave-event', self.control_area_enter_leave_cb)

        # Add the control area to the UI...
        self.stage.add(self.control_area)
        self.control_area.set_opacity(0)

        # Add the start screen:
        self.start_screen = StartScreen()
        self.stage.add(self.start_screen)

        # Fade in the control area on mouse movements...
        self.stage.connect('motion-event', self.motion_event_cb)
        self.start_screen.connect('show-open-dialog', lambda *args: self.emit('show-open-dialog'))


    def set_animate_transition(self, value):
        self.animate_transition = value


    def add_image(self, path):
        self.images.append(Image(path))

        if self.current_image == None:
            self.show_image(0, animate=True)


    def load_image(self, img, async=False):
        """ Load the image with the given ID... """

        self.images[img].load(async)


    def show_image(self, img, animate=True):
        """
        Show the given image.

        :param img: The ID of the image.
        :type img: `int`
        :param animate: Animate the transition?
        :type animate: `bool`
        """

        if self.current_image == None:
            self.start_screen.fade_out()

        # Load the image...
        self.load_image(img)

        # Preload the next image...
        try:
            self.load_image(img + 1, async=True)
        except:
            pass

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
        else:
            old_image.set_opacity(0)
            self.images[self.current_image].set_opacity(255)

        self.calculate_image_position(self.images[self.current_image])

        return False


    def motion_event_cb(self, stage, event):

        if self.current_image == None:
            return

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
        self.start_screen.set_size(allocation.width, allocation.height)

        if self.current_image != None:
            self.calculate_image_position(self.images[self.current_image])

        self.control_area.set_position((allocation.width - self.control_area.get_size()[0]) / 2, allocation.height - self.control_area.get_size()[1] - 30)


class Monet(cream.Module):
    """ Main class of Monet. """

    def __init__(self):

        cream.Module.__init__(self)

        # Initialize the GUI...
        self.window = gtk.Window()
        self.window.set_title("Monet")

        self.view = ImageView()
        self.view.set_animate_transition(self.config.animate_transition)

        self.view.connect('show-open-dialog', self.show_open_dialog_cb)

        for i in os.listdir(PATH):
            if i.endswith('.png') or i.endswith('.jpg'):
                self.view.add_image(os.path.join(PATH, i))

        self.window.add(self.view)
        self.window.set_size_request(800, 480)
        self.window.show_all()

        self.window.connect('destroy', lambda *args: self.quit())


    def show_open_dialog_cb(self, view):

        dialog = gtk.FileChooserDialog(title="Select a folder...",
                    parent=None,
                    action=gtk.FILE_CHOOSER_ACTION_SELECT_FOLDER,
                    buttons=(gtk.STOCK_CANCEL, gtk.RESPONSE_REJECT, gtk.STOCK_OPEN, gtk.RESPONSE_ACCEPT))
        res = dialog.run()

        if res == gtk.RESPONSE_ACCEPT:
            path = dialog.get_filename()

            for i in os.listdir(path):
                if i.endswith('.png') or i.endswith('.jpg'):
                    self.view.add_image(os.path.join(path, i))

        dialog.hide()


if __name__ == '__main__':
    monet = Monet()
    monet.main()

#! /usr/bin/env python
# -*- coding: utf-8 -*-

# Copyright (C) 2011 Deepin, Inc.
#               2011 Hou Shaohui
#
# Author:     Hou Shaohui <houshao55@gmail.com>
# Maintainer: Hou ShaoHui <houshao55@gmail.com>
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

from widget.ui import app_theme
from dtk.ui.button import ToggleButton, ImageButton
from dtk.ui.utils import foreach_recursive, is_left_button
from dtk.ui.menu import Menu
import gtk
import utils
from player import Player
from widget.information import PlayInfo
from widget.timer import SongTimer, VolumeSlider
from widget.equalizer import equalizer_win
from widget.cover import PlayerCoverButton
from widget.lyrics_module import lyrics_display

from source.local import ImportFolderJob
from library import MediaDB
from config import config


class HeaderBar(gtk.HBox):
    def __init__(self):
        super(HeaderBar, self).__init__()
        self.set_border_width(5)
        
        # cover box
        self.cover_box = PlayerCoverButton()
        
        # swap played status handler
        Player.connect("played", self.__swap_play_status, True)
        Player.connect("paused", self.__swap_play_status, False)
        Player.connect("stopped", self.__swap_play_status, False)
        Player.connect("play-end", self.__swap_play_status, False)
        config.connect("config-changed", self.sycnh_status)
        
        # play button
        play_status_pixbuf = app_theme.get_pixbuf("action/play.png")
        pause_status_pixbuf = app_theme.get_pixbuf("action/pause.png")
        self.__play = ToggleButton(play_status_pixbuf, pause_status_pixbuf)
        self.__id_signal_play = self.__play.connect("toggled", lambda w: Player.playpause())
        
        prev = self.__create_button("previous")
        next = self.__create_button("next")
        
        self.vol = VolumeSlider()
        song_timer = SongTimer()
        
        mainbtn = gtk.HBox(spacing=3)
        prev_align = gtk.Alignment()
        prev_align.set(0.5, 0.5, 0, 0)
        prev_align.add(prev)
        
        next_align = gtk.Alignment()
        next_align.set(0.5, 0.5, 0, 0)
        next_align.add(next)
        
        mainbtn.pack_start(prev_align, False, False)
        mainbtn.pack_start(self.__play, False, False)
        mainbtn.pack_start(next_align, False, False)
        
        topbox = gtk.HBox()
        topbox.pack_start(PlayInfo(),True, True)
        topbox.pack_start(mainbtn, False, False)
        
        control_box = gtk.VBox(spacing=3)
        control_box.pack_start(topbox, False, False)
        control_box.pack_start(song_timer, False, False)
        
        plugs_box = gtk.HBox()
        more_box = gtk.HBox(False, 10)
        more_align = gtk.Alignment()
        more_align.set(1.0, 0, 0, 0)
        
        # test
        self.lyrics_button = self.__create_simple_toggle_button("lyrics", self.start_lyrics)
        musicbox_button = self.__create_simple_toggle_button("musicbox", self.open_dir)
        media_button = self.__create_simple_toggle_button("media", self.save_db)
        playlist_button = self.__create_simple_toggle_button("playlist", self.start_playlist)
        
        
        more_box.pack_start(playlist_button)
        more_box.pack_start(self.lyrics_button)
        more_box.pack_start(musicbox_button)
        more_box.pack_start(media_button)
        more_align.add(more_box)        
        
        volume_align = gtk.Alignment()
        volume_align.set(0, 1.0, 0, 0)
        volume_align.add(self.vol)

        plugs_box.pack_start(volume_align, False, False)
        plugs_box.pack_start(more_align, True, True)        
        control_box.pack_start(plugs_box, False, False)
        information = gtk.HBox(spacing=6)
        information.pack_start(self.cover_box, False, False)
        information.pack_start(control_box, True, True)
        self.pack_start(information, True, True)
        self.load_config()
                
        # right click
        foreach_recursive(self, lambda w: w.connect("button-press-event", self.right_click_cb))
        
    def load_config(self):    
        if config.getboolean("lyrics", "status"):
            self.lyrics_button.set_active(True)
        else:    
            self.lyrics_button.set_active(False)
        
    def open_dir(self, widget):    
        MediaDB.full_erase("local")
        ImportFolderJob()
            
    def __create_simple_toggle_button(self, name, callback):
        toggle_button = ToggleButton(
            app_theme.get_pixbuf("control/%s_normal.png" % name),
            app_theme.get_pixbuf("control/%s_hover.png" % name))
        toggle_button.connect("toggled", callback)
        return toggle_button

    def sycnh_status(self, config, selection, option, value):
        if selection == "lyrics" and option == "status":
            if not config.getboolean("lyrics", "status"):
                self.lyrics_button.set_active(False)
                
    
    def start_lyrics(self, widget):        
        if widget.get_active():
            lyrics_display.run()
        else:    
            lyrics_display.hide_all()
            
    def start_playlist(self, widget):        
        pass
            
    def save_db(self, widget):    
        MediaDB.save()
        Player.save_state()
        config.write()
        
    def right_click_cb(self, widget, event):    
        if event.button == 3:
            Menu([(None, "均衡器", lambda : equalizer_win.run())]).show((int(event.x_root), int(event.y_root)))
                
                    
    def __swap_play_status(self, obj, active):    
        self.__play.handler_block(self.__id_signal_play)
        self.__play.set_active(active)
        self.__play.handler_unblock(self.__id_signal_play)
        
        
    def __create_button(self, name, tip_msg=None):    
        button = ImageButton(
            app_theme.get_pixbuf("action/%s_normal.png" % name),
            app_theme.get_pixbuf("action/%s_normal.png" % name),
            app_theme.get_pixbuf("action/%s_hover.png" % name),
            )
        button.connect("clicked", self.player_control, name)
        # todo tip
        return button
    
    def player_control(self, button, name):
        if name == "next":
            getattr(Player, name)(True)
        else:    
            getattr(Player, name)()

            
header_bar = HeaderBar()            
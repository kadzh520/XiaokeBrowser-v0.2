# -*- coding: utf-8 -*-
#没有人比我更懂晓柯浏览器
# XiaoKe v0.2
import wx
import wx.aui
import wx.xrc
import wx.html2
from configparser import ConfigParser
import tkinter as tk
from tkinter import messagebox
import sys
import os
import urllib.parse
import shutil
import re
from typing import cast
#获取配置
conf = ConfigParser()
conf.read('config.ini') 
Engine = None
if conf['Engine']['Engine'] == 'Default':
    Engine = wx.html2.WebViewBackendDefault
elif conf['Engine']['Engine'] == 'IE':
    Engine = wx.html2.WebViewBackendIE
elif conf['Engine']['Engine'] == 'Edge':
    Engine = wx.html2.WebViewBackendEdge
elif conf['Engine']['Engine'] == 'WebKit':
    root = tk.Tk()
    root.withdraw()
    messagebox.showerror("Error", "webkit浏览器引擎目前不支持!!!")
    root.mainloop()
else:
    root = tk.Tk()
    root.withdraw()
    messagebox.showerror("Error", "config.ini的浏览器引擎不支持!!!")
    root.mainloop()

###########################################################################
## Class MyFrame1
###########################################################################
class MyFrame(wx.Frame):
    def __init__(self):
        wx.Frame.__init__(self, None, title='Full Screen Window', style=wx.NO_BORDER | wx.STAY_ON_TOP)
        self.ShowFullScreen(False)
        self.Bind(wx.EVT_KEY_DOWN, self.OnKeyDown)

    def OnKeyDown(self, event):
        keycode = event.GetKeyCode()
        if keycode == wx.WXK_F11:
            self.Maximize()
class MyFrame2(wx.Frame):
    def __init__(self, parent):
        wx.Frame.__init__(self, parent, id=wx.ID_ANY, title=u"关于晓柯", pos=wx.DefaultPosition,
                          size=wx.Size(715, 412), style=wx.DEFAULT_FRAME_STYLE | wx.RESIZE_BORDER)
        self.icon = wx.Icon('ico.ico', wx.BITMAP_TYPE_ICO)
        self.SetIcon(self.icon)
        self.SetSizeHints(wx.DefaultSize, wx.DefaultSize)
    
        self.SetMinSize(wx.Size(715, 412))
        self.SetMaxSize(wx.Size(715, 412))

        # 禁用最大化和最小化按钮
        self.SetWindowStyle(self.GetWindowStyle() & ~(wx.MAXIMIZE_BOX | wx.MINIMIZE_BOX))

        bSizer1 = wx.BoxSizer(wx.VERTICAL)
        #chgskj.cn
        self.browser = wx.html2.WebView.New(self, backend=Engine)
        self.browser.LoadURL("https://www.chgskj.cn")
        
        bSizer1.Add(self.browser, 1, wx.EXPAND)
        
        self.SetSizer(bSizer1)
        self.Layout()

        self.Centre(wx.BOTH)
    

    def __del__(self):
        pass
class Tab(wx.Panel):
    def __init__(self, parent):
        wx.Panel.__init__(self, parent)
        sizer = wx.BoxSizer(wx.VERTICAL)
        self.browser = wx.html2.WebView.New(self, backend=Engine)
        self.browser.LoadURL("https://www.baidu.com")
        
        sizer.Add(self.browser, proportion=1, flag=wx.EXPAND)
        self.SetSizer(sizer)

class MyFrame1 ( wx.Frame ):

    def __init__( self, parent ):
        wx.Frame.__init__ ( self, parent, id = wx.ID_ANY, title = u"晓柯浏览器 - 一款轻量高效、性能发挥到位的浏览器", pos = wx.DefaultPosition, size = wx.Size( 1026,747 ), style = wx.DEFAULT_FRAME_STYLE|wx.TAB_TRAVERSAL )
        self.icon = wx.Icon('ico.ico', wx.BITMAP_TYPE_ICO)
        self.SetIcon(self.icon)
        menu_bar = wx.MenuBar()
        self.SetMenuBar(menu_bar)

        file_menu = wx.Menu()
        operation_menu = wx.Menu()
        about_menu = wx.Menu()
        engine_menu = wx.Menu()
        self.star_menu = wx.Menu()
        self.history_menu = wx.Menu()

        file_menu.Append(wx.ID_FILE6,"打开文件")
        file_menu.Append(wx.ID_FILE7,"另存为")
        file_menu.Append(wx.ID_FILE8,"打印")


        operation_menu.Append(wx.ID_NEW, "新建网页")
        operation_menu.Append(wx.ID_CLOSE, "关闭网页")
        operation_menu.Append(wx.ID_RESET,"重新加载当前网页")
        operation_menu.Append(wx.ID_FORWARD, "下一页")
        operation_menu.Append(wx.ID_BACKWARD, "上一页")

        about_menu.Append(wx.ID_ABOUT,"关于晓柯浏览器")

        engine_menu.Append(wx.ID_FILE1,"IE引擎")
        engine_menu.Append(wx.ID_FILE2,"默认引擎")
        #engine_menu.Append(wx.ID_FILE3,"WebKit引擎")
        engine_menu.Append(wx.ID_FILE4,"Edge引擎")

        self.star_menu.Append(wx.ID_FILE5,"收藏当前网页")
        self.star_menu.AppendSeparator()

        menu_bar.Append(file_menu,"文件")

        menu_bar.Append(operation_menu, "编辑")

        menu_bar.Append(engine_menu,"引擎")

        menu_bar.Append(self.star_menu,"收藏夹")

        menu_bar.Append(self.history_menu,"历史记录")

        menu_bar.Append(about_menu,"帮助")

        self.SetSizeHints( wx.DefaultSize, wx.DefaultSize )

        main_sizer = wx.BoxSizer( wx.VERTICAL )

        toolbar_sizer = wx.BoxSizer( wx.HORIZONTAL )


        main_sizer.Add( toolbar_sizer, 0, 0, 5 )

        search_bar_sizer = wx.BoxSizer( wx.HORIZONTAL )

        self.m_searchCtrl2 = wx.SearchCtrl( self, wx.ID_ANY, wx.EmptyString, wx.DefaultPosition, wx.DefaultSize, 0 )
        self.m_searchCtrl2.ShowSearchButton( True )
        self.m_searchCtrl2.ShowCancelButton( False )
        search_bar_sizer.Add( self.m_searchCtrl2, 1, wx.EXPAND|wx.TOP|wx.RIGHT|wx.LEFT, 5 )

        self.m_button4 = wx.Button( self, wx.ID_ANY, u"搜索", wx.DefaultPosition, wx.DefaultSize, 0 )
        search_bar_sizer.Add( self.m_button4, 0, wx.TOP|wx.RIGHT|wx.LEFT, 5 )


        main_sizer.Add( search_bar_sizer, 0, wx.EXPAND|wx.BOTTOM, 5 )
        self.tab_container_sizer = wx.BoxSizer( wx.VERTICAL )


        main_sizer.Add( self.tab_container_sizer, 1, wx.EXPAND, 5 )
        
        #self.browser = wx.html2.WebView.New(self)
        #self.browser.LoadURL("https://www.baidu.com")
        self.m_searchCtrl2.SetValue("https://www.baidu.com")
        #self.tab_container_sizer.Add( self.browser, 1, wx.ALL|wx.EXPAND, 5 )
        # Panel creation and tab holder setup:
        self.tab_notebook = wx.aui.AuiNotebook(self)
        # Initiation of the tab windows:
        tab = Tab(self.tab_notebook)
        

        # Assigning names to tabs and adding them:
        self.tab_notebook.AddPage(tab, "Loading...")
        #tab_notebook.AddPage()

        # Organizing notebook layout using a sizer:
        self.tab_container_sizer.Add(self.tab_notebook, 1, wx.EXPAND)

        
        self.SetSizer( main_sizer )
        self.Layout()

        self.Centre( wx.BOTH )

        tab = self.get_current_tab()

        self.m_button4.Bind( wx.EVT_BUTTON,self.load_url)
        self.Bind(wx.EVT_KEY_DOWN, self.OnKeyDown)
        self.Bind(wx.EVT_SEARCHCTRL_SEARCH_BTN,self.load_url)
        self.Bind(wx.EVT_MENU, self.new_html, id=wx.ID_NEW)
        self.Bind(wx.EVT_MENU, self.close_html, id=wx.ID_CLOSE)
        self.Bind(wx.EVT_MENU, self.reset_html,  id=wx.ID_RESET)
        self.Bind(wx.EVT_MENU, self.forward_html, id=wx.ID_FORWARD)
        self.Bind(wx.EVT_MENU, self.backward_html, id=wx.ID_BACKWARD)
        self.Bind(wx.EVT_MENU, self.IE_html, id=wx.ID_FILE1)
        self.Bind(wx.EVT_MENU, self.Chrome_html, id=wx.ID_FILE2)
        #self.Bind(wx.EVT_MENU, self.WebKit_html, id=wx.ID_FILE3)
        self.Bind(wx.EVT_MENU, self.Edge_html, id=wx.ID_FILE4)
        self.Bind(wx.EVT_MENU, self.about_html, id=wx.ID_ABOUT)
        self.Bind(wx.EVT_MENU, self.star_html, id=wx.ID_FILE5)
        self.Bind(wx.EVT_MENU, self.open_file, id=wx.ID_FILE6)
        self.Bind(wx.EVT_MENU, self.save_file, id=wx.ID_FILE7)
        self.Bind(wx.EVT_MENU, self.print_file, id=wx.ID_FILE8)
        tab.browser.Bind(wx.html2.EVT_WEBVIEW_NEWWINDOW, self.on_link_clicked)
        tab.browser.Bind(wx.html2.EVT_WEBVIEW_LOADED, self.OnLoaded)
        tab.browser.Bind(wx.html2.EVT_WEBVIEW_TITLE_CHANGED, self.OnTitleChanged)
        self.Bind(wx.EVT_CLOSE, self.OnClose)
        self.timer = wx.Timer(self)
        self.timer.Start(10)
        self.Bind(wx.EVT_TIMER, self.OnTimer)


    def __del__( self ):
        pass
    def get_current_tab(self):
        page = self.tab_notebook.GetSelection()
        return cast(Tab, self.tab_notebook.GetPage(page))
    def parse_url(self,url):
        url = str(url)
        if os.path.isfile(url):
            return url
        elif url.startswith('http://') or url.startswith('https://'):
            return url
        else:
            url = 'http://' + url
            return url
    def OnKeyDown(self, event):
        keycode = event.GetKeyCode()
        tab = self.get_current_tab()
        url = tab.browser.GetCurrentURL()
        if keycode == wx.WXK_F11:
            self.frame3_url = url
            
    def OnTimer(self,_event):
        count = self.tab_notebook.GetPageCount()
        if count == 0:
            self.Close()
            wx.GetApp().ExitMainLoop()
    def OnClose(self,_event):
        self.Close()
        wx.GetApp().ExitMainLoop()

    def star_html(self,_event):
        tab = self.get_current_tab()
        url = tab.browser.GetCurrentURL()
        self.menu_id = wx.Window.NewControlId()
        menu_item = self.star_menu.Append(self.menu_id, url)
        self.Bind(wx.EVT_MENU, self.open_url, menu_item)

    def open_url(self, event):
        menu_id = event.GetId()
        menu_item = self.star_menu.FindItemById(menu_id)
        if menu_item is None:
            menu_item = self.history_menu.FindItemById(menu_id)
        if menu_item is not None:
            menu_item_label = menu_item.GetItemLabel()
            tab = self.get_current_tab()
            tab.browser.LoadURL(menu_item_label)
        else:
            self.warning_message("程序发生了一次错误,错误码:0x01 请你马上到客户群进行反馈")
    def is_url(self,string):
        regex = re.compile(
            r'^https?://'  # http:// 或 https://
            r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+(?:[A-Z]{2,6}\.?|[A-Z0-9-]{2,}\.?)|'  # 域名部分（例如 www.example.com）
            r'localhost|'  # localhost
            r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})'  # IP 地址部分
            r'(?::\d+)?'  # 端口号（可选）
            r'(?:/?|[/?]\S+)$', re.IGNORECASE)
        return re.match(regex, string) is not None
    def about_html(self,_event):
        frame = MyFrame2(None)
        frame.Show()
    def update_history(self,_event):
        tab = self.get_current_tab()
        url = tab.browser.GetCurrentURL()
        self.menu_id = wx.Window.NewControlId()
        menu_item = self.history_menu.Append(self.menu_id, url)
        self.Bind(wx.EVT_MENU, self.open_url, menu_item)
    def open_file(self,_event):
        # 创建一个带有标题和默认文件名的文件对话框
        dlg = wx.FileDialog(None, "选择文件", "", "", "*.*", wx.FD_OPEN)

        # 如果选择了文件，则打印文件路径
        if dlg.ShowModal() == wx.ID_OK:
            filepath = dlg.GetPath()
        # 关闭对话框
        dlg.Destroy()
        tab = self.get_current_tab()
        tab.browser.LoadURL(filepath)
    def save_file(self,_event):
        filepath = self.m_searchCtrl2.GetValue()
        #判断是不是url
        if self.is_url(filepath):
            return None
        dlg = wx.FileDialog(self, message="Save file as ...", defaultDir=".", defaultFile="", style=wx.FD_SAVE)
        #去除掉开头部分
        filepath = filepath.replace("file:///", "")
        if dlg.ShowModal() == wx.ID_OK:
            path = dlg.GetPath()
            shutil.copy(filepath, path)
        dlg.Destroy()
    def print_file(self,_event):
        tab = self.get_current_tab()
        tab.browser.Print()
    def warning_message(self,str):
        root = tk.Tk()
        root.withdraw()
        answer = messagebox.askyesno("警告", str)
    
        if answer:
            # 重启当前程序
            python = sys.executable
            root.destroy()
            os.execl(python, python, *sys.argv)

    def IE_html(self,_event):
        conf.set('Engine', 'Engine', 'IE')

        # 保存修改后的ini文件
        with open('config.ini', 'w') as config_file:
            conf.write(config_file)
        self.warning_message("是否切换到IE引擎?")


    def Chrome_html(self,_event):
        conf.set('Engine', 'Engine', 'Default')

        # 保存修改后的ini文件
        with open('config.ini', 'w') as config_file:
            conf.write(config_file)
        self.warning_message("是否切换到默认引擎?")


    def WebKit_html(self,_event):
        conf.set('Engine', 'Engine', 'WebKit')

        # 保存修改后的ini文件
        with open('config.ini', 'w') as config_file:
            conf.write(config_file)
        self.warning_message("是否切换到WebKit引擎?")


    def Edge_html(self,_event):
        conf.set('Engine', 'Engine', 'Edge')

        # 保存修改后的ini文件
        with open('config.ini', 'w') as config_file:
            conf.write(config_file)
        self.warning_message("是否切换到Edge引擎?")


    def OnTitleChanged(self,event):
        title = event.GetString()
        page = self.tab_notebook.GetSelection()
        self.tab_notebook.SetPageText(page,title)
    def new_html(self,_event):
        page = Tab(self.tab_notebook)
        self.tab_notebook.AddPage(page, "Loading...")
        self.tab_notebook.SetSelection(self.tab_notebook.GetPageIndex(page))
        tab = self.get_current_tab()
        tab.browser.Bind(wx.html2.EVT_WEBVIEW_NEWWINDOW, self.on_link_clicked)
        tab.browser.Bind(wx.html2.EVT_WEBVIEW_LOADED, self.OnLoaded)
        tab.browser.Bind(wx.html2.EVT_WEBVIEW_TITLE_CHANGED, self.OnTitleChanged)
    def close_html(self,_event):
        page = self.tab_notebook.GetSelection()
        self.tab_notebook.DeletePage(page)
    def reset_html(self,_event):
        tab = self.get_current_tab()
        tab.browser.Reload()
    def forward_html(self,_event):
        tab = self.get_current_tab()
        if tab.browser.CanGoForward():
            tab.browser.GoForward()
        else:
            pass
    def backward_html(self,_event):
        tab = self.get_current_tab()
        if tab.browser.CanGoBack():
            tab.browser.GoBack()
        else:
            pass
    def on_link_clicked(self,event):
        self.new_html(None)
        url = event.GetURL()
        tab = self.get_current_tab()
        tab.browser.LoadURL(url)
        self.m_searchCtrl2.SetValue(url)
        
    def OnLoaded(self, event):
        url = event.GetURL()
        url = urllib.parse.unquote(url, 'utf-8')  # 解码URL
        self.m_searchCtrl2.SetValue(url)
        self.update_history(None)
    def load_url(self,_event):
        search_url = self.m_searchCtrl2.GetValue()  
        search_url = self.parse_url(search_url)
        tab = self.get_current_tab()
        tab.browser.LoadURL(search_url)
        self.m_searchCtrl2.SetValue(search_url)

app = wx.App(False)
frame = MyFrame1(None)
frame.Show()
app.MainLoop()



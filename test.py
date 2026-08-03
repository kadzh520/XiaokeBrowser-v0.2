# -*- coding: utf-8 -*-
# 没有人比我更懂晓柯浏览器
# 由OpticsValley强力重构
# 从此之后，此项目不再维护，这是最终版本
# XiaoKe v0.2

from __future__ import annotations

import os
import re
import shutil
import sys
import tempfile
import urllib.parse
from configparser import ConfigParser
from pathlib import Path
from typing import Optional

import wx
import wx.aui
import wx.html2


# ============================================================================
# 应用常量与配置
# ============================================================================

APP_NAME = "晓柯浏览器"
APP_VERSION = "v0.2.2.0128"
APP_TITLE = f"{APP_NAME} - 一款轻量高效、性能发挥到位的浏览器"
HOME_URL = "https://www.baidu.com"
MAX_HISTORY_ITEMS = 100
DEFAULT_ENGINE_NAME = "Edge"

BASE_DIR = Path(__file__).resolve().parent
CONFIG_PATH = BASE_DIR / "config.ini"
ICON_PATH = BASE_DIR / "ico.ico"

ENGINE_BACKENDS = {
    "Edge": wx.html2.WebViewBackendEdge,
    "IE": wx.html2.WebViewBackendIE,
}


def is_backend_available(backend: str) -> bool:
    """安全检查 WebView 引擎是否可用。"""
    try:
        return bool(wx.html2.WebView.IsBackendAvailable(backend))
    except (AttributeError, RuntimeError):
        return backend == wx.html2.WebViewBackendDefault


def load_config() -> tuple[ConfigParser, str, Optional[str]]:
    """加载配置，并在配置缺失、损坏或引擎不可用时回退到默认引擎。"""
    config = ConfigParser()
    warning = None

    try:
        config.read(CONFIG_PATH, encoding="utf-8")
    except (OSError, UnicodeError):
        warning = "config.ini 无法读取，已临时使用默认浏览器引擎。"

    if not config.has_section("Engine"):
        config.add_section("Engine")

    engine_name = config.get("Engine", "Engine", fallback=DEFAULT_ENGINE_NAME).strip()

    # 兼容旧版配置：原来的 Default 选项现在统一迁移为 Edge。
    if engine_name == "Default":
        engine_name = DEFAULT_ENGINE_NAME

    backend = ENGINE_BACKENDS.get(engine_name)

    if backend is None:
        warning = f"配置中的浏览器引擎“{engine_name}”不受支持，已回退到 Edge 引擎。"
        engine_name = DEFAULT_ENGINE_NAME
        backend = ENGINE_BACKENDS[engine_name]

    if not is_backend_available(backend):
        warning = f"当前系统无法使用“{engine_name}”引擎，已临时使用系统 WebView 引擎。"
        backend = wx.html2.WebViewBackendDefault

    config.set("Engine", "Engine", engine_name)
    return config, backend, warning


def save_config(config: ConfigParser) -> None:
    """先写临时文件再替换配置，避免程序中断时留下半截配置文件。"""
    temporary_path: Optional[Path] = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="w",
            encoding="utf-8",
            newline="",
            dir=BASE_DIR,
            prefix="config-",
            suffix=".tmp",
            delete=False,
        ) as temporary_file:
            config.write(temporary_file)
            temporary_path = Path(temporary_file.name)
        os.replace(temporary_path, CONFIG_PATH)
    except OSError:
        if temporary_path is not None:
            try:
                temporary_path.unlink(missing_ok=True)
            except OSError:
                pass
        raise


CONFIG, WEBVIEW_BACKEND, CONFIG_WARNING = load_config()


# ============================================================================
# 通用辅助函数
# ============================================================================

def normalize_address(value: str) -> Optional[str]:
    """把路径、网址、域名或普通搜索词转换成 WebView 可加载的地址。"""
    value = value.strip()
    if not value:
        return None

    local_path = Path(value).expanduser()
    if local_path.is_file():
        return local_path.resolve().as_uri()

    parsed = urllib.parse.urlparse(value)
    if parsed.scheme in {"http", "https", "file"}:
        return value

    # 没有协议但形似域名/IP时，将其作为 HTTPS 地址处理。
    if re.match(r"^(localhost|\d{1,3}(?:\.\d{1,3}){3}|[^/\s]+\.[^/\s]+)(:\d+)?(?:/.*)?$", value):
        return f"https://{value}"

    # 其他内容作为搜索词，避免生成诸如 http://中文 空格 的无效地址。
    return f"https://www.baidu.com/s?wd={urllib.parse.quote_plus(value)}"


def file_url_to_path(url: str) -> Optional[Path]:
    """将 file:// URL 转换成本地路径；非本地文件地址返回 None。"""
    parsed = urllib.parse.urlparse(url)
    if parsed.scheme.lower() != "file":
        return None

    path_text = urllib.parse.unquote(parsed.path)
    if parsed.netloc:
        path_text = f"//{parsed.netloc}{path_text}"
    if os.name == "nt" and re.match(r"^/[A-Za-z]:", path_text):
        path_text = path_text[1:]
    return Path(path_text)


def show_error(parent: Optional[wx.Window], message: str) -> None:
    wx.MessageBox(message, "错误", wx.OK | wx.ICON_ERROR, parent)


# ============================================================================
# 浏览器标签页
# ============================================================================

class BrowserTab(wx.Panel):
    """单个浏览器标签页，负责持有一个 WebView。"""

    def __init__(self, parent: wx.Window, backend: str, initial_url: str = HOME_URL):
        super().__init__(parent)
        self.browser = wx.html2.WebView.New(self, backend=backend)

        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(self.browser, 1, wx.EXPAND)
        self.SetSizer(sizer)

        self.browser.LoadURL(initial_url)


def set_window_icon(window: wx.TopLevelWindow) -> None:
    """图标缺失时保持程序可运行，而不是在启动阶段崩溃。"""
    if not ICON_PATH.is_file():
        return
    try:
        window.SetIcon(wx.Icon(str(ICON_PATH), wx.BITMAP_TYPE_ICO))
    except (OSError, RuntimeError):
        pass


# ============================================================================
# 主窗口
# ============================================================================

class BrowserFrame(wx.Frame):
    """晓柯浏览器主窗口。"""

    def __init__(self, backend: str, config: ConfigParser):
        super().__init__(None, title=APP_TITLE, size=wx.Size(1026, 747))
        self.backend = backend
        self.config = config
        self._closing = False
        self._favorite_urls: list[str] = []
        self._history_urls: list[str] = []
        self._menu_urls: dict[int, str] = {}
        self._favorite_delete_urls: dict[int, str] = {}
        self._history_delete_urls: dict[int, str] = {}
        self._favorite_dynamic_ids: set[int] = set()
        self._history_dynamic_ids: set[int] = set()
        self._id_refs: list[wx.WindowIDRef] = []

        set_window_icon(self)
        self._create_menu_bar()
        self._create_layout()
        self._bind_frame_events()
        self.create_tab(HOME_URL)

        self.Centre()

    # ------------------------------------------------------------------
    # 界面构建与事件绑定
    # ------------------------------------------------------------------

    def _new_control_id(self) -> int:
        """保留 WindowIDRef，防止 wxPython 提前回收动态菜单 ID。"""
        id_ref = wx.NewIdRef()
        self._id_refs.append(id_ref)
        return int(id_ref)

    def _create_menu_bar(self) -> None:
        menu_bar = wx.MenuBar()

        file_menu = wx.Menu()
        file_menu.Append(wx.ID_OPEN, "打开文件\tCtrl+O")
        file_menu.Append(wx.ID_SAVEAS, "另存为")
        file_menu.Append(wx.ID_PRINT, "打印\tCtrl+P")
        file_menu.AppendSeparator()
        file_menu.Append(wx.ID_EXIT, "退出\tAlt+F4")

        operation_menu = wx.Menu()
        operation_menu.Append(wx.ID_NEW, "新建网页\tCtrl+T")
        operation_menu.Append(wx.ID_CLOSE, "关闭网页\tCtrl+W")
        operation_menu.Append(wx.ID_REFRESH, "重新加载当前网页\tF5")
        self.force_reload_id = self._new_control_id()
        operation_menu.Append(self.force_reload_id, "强制刷新当前网页\tCtrl+F5")
        operation_menu.Append(wx.ID_FORWARD, "下一页\tAlt+Right")
        operation_menu.Append(wx.ID_BACKWARD, "上一页\tAlt+Left")

        engine_menu = wx.Menu()
        self.engine_ids = {
            self._new_control_id(): "Edge",
            self._new_control_id(): "IE",
        }
        engine_labels = {"Edge": "Edge引擎（默认）", "IE": "IE浏览器"}
        for menu_id, engine_name in self.engine_ids.items():
            engine_menu.Append(menu_id, engine_labels[engine_name])

        self.favorite_menu = wx.Menu()
        self.add_favorite_id = self._new_control_id()
        self.clear_favorites_id = self._new_control_id()

        self.history_menu = wx.Menu()
        self.clear_history_id = self._new_control_id()

        help_menu = wx.Menu()
        help_menu.Append(wx.ID_ABOUT, "关于晓柯浏览器")

        menu_bar.Append(file_menu, "文件")
        menu_bar.Append(operation_menu, "编辑")
        menu_bar.Append(engine_menu, "引擎")
        menu_bar.Append(self.favorite_menu, "收藏夹")
        menu_bar.Append(self.history_menu, "历史记录")
        menu_bar.Append(help_menu, "帮助")
        self.SetMenuBar(menu_bar)
        self._rebuild_favorite_menu()
        self._rebuild_history_menu()

    def _create_layout(self) -> None:
        main_sizer = wx.BoxSizer(wx.VERTICAL)
        address_sizer = wx.BoxSizer(wx.HORIZONTAL)

        self.address_ctrl = wx.SearchCtrl(self, style=wx.TE_PROCESS_ENTER)
        self.address_ctrl.ShowSearchButton(True)
        self.address_ctrl.ShowCancelButton(False)
        self.address_ctrl.SetValue(HOME_URL)

        self.search_button = wx.Button(self, label="打开")
        address_sizer.Add(self.address_ctrl, 1, wx.EXPAND | wx.ALL, 5)
        address_sizer.Add(self.search_button, 0, wx.TOP | wx.RIGHT | wx.BOTTOM, 5)

        self.notebook = wx.aui.AuiNotebook(
            self,
            style=wx.aui.AUI_NB_DEFAULT_STYLE | wx.aui.AUI_NB_TAB_MOVE,
        )

        main_sizer.Add(address_sizer, 0, wx.EXPAND)
        main_sizer.Add(self.notebook, 1, wx.EXPAND)
        self.SetSizer(main_sizer)
        self.CreateStatusBar()

    def _bind_frame_events(self) -> None:
        self.search_button.Bind(wx.EVT_BUTTON, self.on_load_address)
        self.address_ctrl.Bind(wx.EVT_TEXT_ENTER, self.on_load_address)
        self.address_ctrl.Bind(wx.EVT_SEARCHCTRL_SEARCH_BTN, self.on_load_address)

        menu_handlers = {
            wx.ID_OPEN: self.on_open_file,
            wx.ID_SAVEAS: self.on_save_file,
            wx.ID_PRINT: self.on_print,
            wx.ID_EXIT: lambda _event: self.Close(),
            wx.ID_NEW: lambda _event: self.create_tab(HOME_URL),
            wx.ID_CLOSE: self.on_close_tab,
            wx.ID_REFRESH: self.on_reload,
            self.force_reload_id: self.on_force_reload,
            wx.ID_FORWARD: self.on_forward,
            wx.ID_BACKWARD: self.on_backward,
            wx.ID_ABOUT: self.on_about,
            self.add_favorite_id: self.on_add_favorite,
            self.clear_favorites_id: self.on_clear_favorites,
            self.clear_history_id: self.on_clear_history,
        }
        for menu_id, handler in menu_handlers.items():
            self.Bind(wx.EVT_MENU, handler, id=menu_id)
        for menu_id in self.engine_ids:
            self.Bind(wx.EVT_MENU, self.on_change_engine, id=menu_id)

        self.Bind(wx.EVT_CHAR_HOOK, self.on_key_down)
        self.Bind(wx.EVT_CLOSE, self.on_close)
        self.notebook.Bind(wx.aui.EVT_AUINOTEBOOK_PAGE_CHANGED, self.on_page_changed)

    def _bind_browser_events(self, tab: BrowserTab) -> None:
        tab.browser.Bind(wx.html2.EVT_WEBVIEW_NEWWINDOW, self.on_new_window)
        tab.browser.Bind(wx.html2.EVT_WEBVIEW_LOADED, self.on_page_loaded)
        tab.browser.Bind(wx.html2.EVT_WEBVIEW_TITLE_CHANGED, self.on_title_changed)
        tab.browser.Bind(wx.html2.EVT_WEBVIEW_ERROR, self.on_webview_error)

    # ------------------------------------------------------------------
    # 标签页与地址导航
    # ------------------------------------------------------------------

    def create_tab(self, url: str, select: bool = True) -> BrowserTab:
        tab = BrowserTab(self.notebook, self.backend, url)
        self._bind_browser_events(tab)
        self.notebook.AddPage(tab, "加载中…", select=select)
        return tab

    def get_current_tab(self) -> Optional[BrowserTab]:
        selection = self.notebook.GetSelection()
        if selection == wx.NOT_FOUND or selection >= self.notebook.GetPageCount():
            return None
        page = self.notebook.GetPage(selection)
        return page if isinstance(page, BrowserTab) else None

    def get_tab_for_browser(self, browser: wx.html2.WebView) -> Optional[BrowserTab]:
        parent = browser.GetParent()
        return parent if isinstance(parent, BrowserTab) else None

    def load_url(self, url: str, tab: Optional[BrowserTab] = None) -> None:
        target_tab = tab or self.get_current_tab()
        if target_tab is None:
            target_tab = self.create_tab(url)
        try:
            target_tab.browser.LoadURL(url)
            if target_tab is self.get_current_tab():
                self.address_ctrl.SetValue(url)
        except RuntimeError as exc:
            show_error(self, f"网页无法加载：\n{exc}")

    def on_load_address(self, _event: wx.Event) -> None:
        url = normalize_address(self.address_ctrl.GetValue())
        if url is None:
            self.SetStatusText("请输入网址、文件路径或搜索内容。")
            return
        self.load_url(url)

    def on_new_window(self, event: wx.html2.WebViewEvent) -> None:
        url = event.GetURL()
        if url:
            self.create_tab(url)

    def on_page_loaded(self, event: wx.html2.WebViewEvent) -> None:
        url = urllib.parse.unquote(event.GetURL(), encoding="utf-8", errors="replace")
        browser = event.GetEventObject()
        current_tab = self.get_current_tab()
        if isinstance(browser, wx.html2.WebView) and self.get_tab_for_browser(browser) is current_tab:
            self.address_ctrl.SetValue(url)
        self._add_history(url)
        self.SetStatusText("加载完成")

    def on_title_changed(self, event: wx.html2.WebViewEvent) -> None:
        browser = event.GetEventObject()
        if not isinstance(browser, wx.html2.WebView):
            return
        tab = self.get_tab_for_browser(browser)
        if tab is None:
            return
        page_index = self.notebook.GetPageIndex(tab)
        if page_index != wx.NOT_FOUND:
            title = event.GetString().strip() or "未命名网页"
            self.notebook.SetPageText(page_index, title)

    def on_page_changed(self, event: wx.aui.AuiNotebookEvent) -> None:
        tab = self.get_current_tab()
        if tab is not None:
            self.address_ctrl.SetValue(tab.browser.GetCurrentURL())
        event.Skip()

    def on_webview_error(self, event: wx.html2.WebViewEvent) -> None:
        message = event.GetString().strip() or "未知错误"
        self.SetStatusText(f"网页加载失败：{message}")

    def on_close_tab(self, _event: wx.Event) -> None:
        count = self.notebook.GetPageCount()
        if count <= 1:
            self.Close()
            return
        selection = self.notebook.GetSelection()
        if selection != wx.NOT_FOUND:
            self.notebook.DeletePage(selection)

    # ------------------------------------------------------------------
    # 浏览操作
    # ------------------------------------------------------------------

    def on_reload(self, _event: wx.Event) -> None:
        tab = self.get_current_tab()
        if tab is not None:
            tab.browser.Reload()

    def on_force_reload(self, _event: wx.Event) -> None:
        """忽略网页缓存，重新向服务器请求当前页面。"""
        tab = self.get_current_tab()
        if tab is not None:
            tab.browser.Reload(wx.html2.WEBVIEW_RELOAD_NO_CACHE)

    def on_forward(self, _event: wx.Event) -> None:
        tab = self.get_current_tab()
        if tab is not None and tab.browser.CanGoForward():
            tab.browser.GoForward()

    def on_backward(self, _event: wx.Event) -> None:
        tab = self.get_current_tab()
        if tab is not None and tab.browser.CanGoBack():
            tab.browser.GoBack()

    def on_key_down(self, event: wx.KeyEvent) -> None:
        if event.GetKeyCode() == wx.WXK_F11:
            self.ShowFullScreen(not self.IsFullScreen())
            return
        event.Skip()

    # ------------------------------------------------------------------
    # 文件操作
    # ------------------------------------------------------------------

    def on_open_file(self, _event: wx.Event) -> None:
        dialog = wx.FileDialog(self, "选择文件", wildcard="所有文件 (*.*)|*.*", style=wx.FD_OPEN)
        try:
            if dialog.ShowModal() != wx.ID_OK:
                return
            path = Path(dialog.GetPath())
        finally:
            dialog.Destroy()

        if not path.is_file():
            show_error(self, "选择的文件不存在或无法访问。")
            return
        self.load_url(path.resolve().as_uri())

    def on_save_file(self, _event: wx.Event) -> None:
        tab = self.get_current_tab()
        if tab is None:
            return

        source = file_url_to_path(tab.browser.GetCurrentURL())
        if source is None or not source.is_file():
            show_error(self, "当前页面不是本地文件，暂时无法使用“另存为”。")
            return

        dialog = wx.FileDialog(
            self,
            "文件另存为",
            defaultFile=source.name,
            wildcard="所有文件 (*.*)|*.*",
            style=wx.FD_SAVE | wx.FD_OVERWRITE_PROMPT,
        )
        try:
            if dialog.ShowModal() != wx.ID_OK:
                return
            destination = Path(dialog.GetPath())
        finally:
            dialog.Destroy()

        try:
            shutil.copy2(source, destination)
        except OSError as exc:
            show_error(self, f"文件保存失败：\n{exc}")

    def on_print(self, _event: wx.Event) -> None:
        tab = self.get_current_tab()
        if tab is None:
            return
        try:
            tab.browser.Print()
        except RuntimeError as exc:
            show_error(self, f"无法打开打印窗口：\n{exc}")

    # ------------------------------------------------------------------
    # 收藏、历史记录与引擎切换
    # ------------------------------------------------------------------

    def _clear_dynamic_menu(
        self,
        menu: wx.Menu,
        dynamic_ids: set[int],
        delete_urls: dict[int, str],
    ) -> None:
        """解除旧动态菜单事件后清空菜单，防止重建时遗留失效 ID。"""
        for menu_id in dynamic_ids:
            self.Unbind(wx.EVT_MENU, id=menu_id)
            self._menu_urls.pop(menu_id, None)
            delete_urls.pop(menu_id, None)
        dynamic_ids.clear()

        for item in list(menu.GetMenuItems()):
            menu.Delete(item)

    def _append_dynamic_item(
        self,
        menu: wx.Menu,
        label: str,
        handler,
        url_map: dict[int, str],
        url: str,
        dynamic_ids: set[int],
    ) -> None:
        """创建由菜单本身管理 ID 生命周期的动态网址条目。"""
        item = menu.Append(wx.ID_ANY, label)
        menu_id = item.GetId()
        url_map[menu_id] = url
        dynamic_ids.add(menu_id)
        self.Bind(wx.EVT_MENU, handler, id=menu_id)

    def _rebuild_favorite_menu(self) -> None:
        self._clear_dynamic_menu(
            self.favorite_menu,
            self._favorite_dynamic_ids,
            self._favorite_delete_urls,
        )
        self.favorite_menu.Append(self.add_favorite_id, "收藏当前网页")
        self.favorite_menu.Append(self.clear_favorites_id, "清空全部收藏")

        if not self._favorite_urls:
            self.favorite_menu.AppendSeparator()
            empty_item = self.favorite_menu.Append(wx.ID_ANY, "暂无收藏")
            empty_item.Enable(False)
            return

        delete_menu = wx.Menu()
        for url in self._favorite_urls:
            self._append_dynamic_item(
                delete_menu,
                url,
                self.on_delete_favorite,
                self._favorite_delete_urls,
                url,
                self._favorite_dynamic_ids,
            )
        self.favorite_menu.AppendSubMenu(delete_menu, "删除单项")
        self.favorite_menu.AppendSeparator()

        for url in self._favorite_urls:
            self._append_dynamic_item(
                self.favorite_menu,
                url,
                self.on_open_saved_url,
                self._menu_urls,
                url,
                self._favorite_dynamic_ids,
            )

    def _rebuild_history_menu(self) -> None:
        self._clear_dynamic_menu(
            self.history_menu,
            self._history_dynamic_ids,
            self._history_delete_urls,
        )
        self.history_menu.Append(self.clear_history_id, "清空全部历史记录")

        if not self._history_urls:
            self.history_menu.AppendSeparator()
            empty_item = self.history_menu.Append(wx.ID_ANY, "暂无历史记录")
            empty_item.Enable(False)
            return

        delete_menu = wx.Menu()
        for url in self._history_urls:
            self._append_dynamic_item(
                delete_menu,
                url,
                self.on_delete_history,
                self._history_delete_urls,
                url,
                self._history_dynamic_ids,
            )
        self.history_menu.AppendSubMenu(delete_menu, "删除单项")
        self.history_menu.AppendSeparator()

        for url in reversed(self._history_urls):
            self._append_dynamic_item(
                self.history_menu,
                url,
                self.on_open_saved_url,
                self._menu_urls,
                url,
                self._history_dynamic_ids,
            )

    def on_add_favorite(self, _event: wx.Event) -> None:
        tab = self.get_current_tab()
        if tab is None:
            return
        url = tab.browser.GetCurrentURL()
        if not url or url in self._favorite_urls:
            self.SetStatusText("该网页已经收藏。")
            return
        self._favorite_urls.append(url)
        self._rebuild_favorite_menu()
        self.SetStatusText("已添加到收藏夹。")

    def _add_history(self, url: str) -> None:
        if not url:
            return

        # 同一网址只保留最近一次记录，并把最新访问的网址放到列表末尾。
        if url in self._history_urls:
            self._history_urls.remove(url)
        self._history_urls.append(url)
        if len(self._history_urls) > MAX_HISTORY_ITEMS:
            self._history_urls.pop(0)
        self._rebuild_history_menu()

    def on_delete_favorite(self, event: wx.CommandEvent) -> None:
        url = self._favorite_delete_urls.get(event.GetId())
        if url is None:
            return
        self._favorite_urls.remove(url)
        self._rebuild_favorite_menu()
        self.SetStatusText("已删除该收藏。")

    def on_delete_history(self, event: wx.CommandEvent) -> None:
        url = self._history_delete_urls.get(event.GetId())
        if url is None:
            return
        self._history_urls.remove(url)
        self._rebuild_history_menu()
        self.SetStatusText("已删除该条历史记录。")

    def on_clear_favorites(self, _event: wx.Event) -> None:
        if not self._favorite_urls:
            self.SetStatusText("收藏夹已经为空。")
            return
        answer = wx.MessageBox(
            "确定要清空全部收藏吗？",
            "清空收藏夹",
            wx.YES_NO | wx.NO_DEFAULT | wx.ICON_WARNING,
            self,
        )
        if answer != wx.YES:
            return
        self._favorite_urls.clear()
        self._rebuild_favorite_menu()
        self.SetStatusText("已清空全部收藏。")

    def on_clear_history(self, _event: wx.Event) -> None:
        if not self._history_urls:
            self.SetStatusText("历史记录已经为空。")
            return
        answer = wx.MessageBox(
            "确定要清空全部历史记录吗？",
            "清空历史记录",
            wx.YES_NO | wx.NO_DEFAULT | wx.ICON_WARNING,
            self,
        )
        if answer != wx.YES:
            return
        self._history_urls.clear()
        self._rebuild_history_menu()
        self.SetStatusText("已清空全部历史记录。")

    def on_open_saved_url(self, event: wx.CommandEvent) -> None:
        url = self._menu_urls.get(event.GetId())
        if url is None:
            self.SetStatusText("对应的网址记录已经失效。")
            return
        self.load_url(url)

    def on_change_engine(self, event: wx.CommandEvent) -> None:
        engine_name = self.engine_ids.get(event.GetId())
        if engine_name is None:
            return

        backend = ENGINE_BACKENDS[engine_name]
        if not is_backend_available(backend):
            show_error(self, f"当前系统无法使用“{engine_name}”引擎。")
            return

        self.config.set("Engine", "Engine", engine_name)
        try:
            save_config(self.config)
        except OSError as exc:
            show_error(self, f"配置保存失败：\n{exc}")
            return

        answer = wx.MessageBox(
            f"浏览器引擎已设置为“{engine_name}”，是否立即重启程序？",
            "切换浏览器引擎",
            wx.YES_NO | wx.ICON_QUESTION,
            self,
        )
        if answer == wx.YES:
            wx.CallAfter(self.restart_application)

    def on_about(self, _event: wx.Event) -> None:
        wx.MessageBox(
            f"软件名：{APP_NAME}\n版本号：{APP_VERSION}",
            f"关于{APP_NAME}",
            wx.OK | wx.ICON_INFORMATION,
            self,
        )

    # ------------------------------------------------------------------
    # 程序生命周期
    # ------------------------------------------------------------------

    def restart_application(self) -> None:
        """使用当前 Python 解释器重新启动程序。"""
        python = sys.executable
        os.execl(python, python, *sys.argv)

    def on_close(self, event: wx.CloseEvent) -> None:
        """只让 wxWidgets 执行一次默认销毁流程，避免 Close 事件递归。"""
        if self._closing:
            event.Skip()
            return
        self._closing = True
        event.Skip()


# ============================================================================
# 程序入口
# ============================================================================

def main() -> int:
    app = wx.App(False)

    if CONFIG_WARNING:
        wx.MessageBox(CONFIG_WARNING, "配置提示", wx.OK | wx.ICON_WARNING)

    frame = BrowserFrame(WEBVIEW_BACKEND, CONFIG)
    frame.Show()
    app.MainLoop()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

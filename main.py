#!/usr/bin/env python
# vim:set ts=4 sw=4 et smartindent fileencoding=utf-8:

# 祭日情報
# https://www8.cao.go.jp/chosei/shukujitsu/gaiyou.html
# https://www8.cao.go.jp/chosei/shukujitsu/syukujitsu.csv
#
import hashlib
import os
import datetime
import requests
import wx
import wx.lib.buttons as Button

# pip install python-dateutil
# 翌月とかの計算用
from dateutil.relativedelta import relativedelta

# オリジナル
from ds import DB, Struct
#from schedule import ScheduleDlg

WEEKDAY_MSG = (u'日', u'月', u'火', u'水', u'木', u'金', u'土')
WEEKDAY_COLOR = (wx.Colour(255, 0, 0), None, None, None, None, None, wx.Colour(0, 0, 255))
DBFILE = os.path.join(os.path.abspath(os.path.dirname(__file__)),
        "weekday.sqlite")
WEEKDAY_URL = 'https://www8.cao.go.jp/chosei/shukujitsu/syukujitsu.csv'
MAX_WEEK = 6 # 一月の最大週

def create_weekday_table(db):
    '''祭日情報のテーブルを作る'''
    db.CreateTable('lastupdate', [
        dict(name = 'cdate', nametype = 'DATETIME', primary = True),
        dict(name = 'hash', nametype = 'TEXT'),
        ])
    db.CreateTable('weekday', [
        dict(name = 'wdate', nametype = 'DATE', primary = True),
        dict(name = 'name', nametype = 'TEXT'),
        ])

def is_weekday_update(ltime):
    '''更新作業が必要かどうか'''
    # 毎月一日以降にになったら更新確認
    n = datetime.datetime.now()
    l = datetime.datetime.strptime(ltime, '%Y-%m-%d')
    # 翌月一日
    nxt = l + relativedelta(months = 1)
    nxt.replace(day = 1)
    return n >= nxt

#def is_web_update(db):
#    '''更新されているか確認する'''
#    # If-Modified-Sinceには対応していない?
#    # のでこの処理は削除
##    ldate = datetime.datetime.strptime(rslt[0][0], '%Y-%m-%d %H:%M:%S')
##    lhttp = formatdate(ldate.timestamp(), usegmt = True)
#    # UTC->JST
#    # ndate='Tue, 27 Aug 2019 07:22:08 GMT'
#    # from email.utils import parsedate_to_datetime
#    # utc=parsedate_to_datetime(ndate)
#    # from dateutil.tz import gettz
#    # jst = utc.astimezone(gettz('Asia/Tokyo'))
#    # -> datetime.datetime(2019, 8, 27, 16, 22, 8, tzinfo=tzfile('/usr/share/zoneinfo/Asia/Tokyo'))
#    pass

def convert_date(days):
    '''yyyy/m/d形式をdatetime.date型で返す'''
    t = days.split('/')
    # 日付の書式がおかしければ下の変換処理で例外が出るはず
    n = map(int, t)
    return datetime.date(*n)

def cal_csv_hash(csvtext):
    h = hashlib.sha512()
    h.update(csvtext)
    return h.hexdigest()

def update_weekday_info(db, lastupdate):
    '''内閣府のウェブページから祭日情報を持ってきて更新する'''
    try:
        res = requests.get(WEEKDAY_URL, timeout = (3.0, 9.0))
    except requests.exceptions.Timeout:
        # タイムアウトしても更新しないだけ
        return True
    if not res.ok:
        return True
    # textはsjisなのにencodingはISO-8859-1の謎
    # ヘッダに文字コード情報がないのが原因?
    res.encoding = 'cp932'
    # hashで変更を確認する
    weekday_csv = res.text
    # CSVファイルのハッシュ値を計算する
    h = hashlib.sha512()
    h.update(weekday_csv.encode('utf8'))
    hash_value = h.hexdigest()
    if lastupdate and hash_value == lastupdate[1]:
        return True
    # hash値を更新する
    if lastupdate:
        key = lastupdate[0]
        db.Replace('lastupdate', cdate = key, hash = hash_value)
    else:
        n = datetime.datetime.now()
        key = n.strftime('%Y-%m-%d')
        db.Insert('lastupdate', cdate = key, hash = hash_value)

    # 内容を更新する
    for l in weekday_csv.splitlines()[1:]:
        t = l.split(',')
        try:
            day = convert_date(t[0].strip())
            name = t[1].strip()
        except (ValueError, IndexError) as e:
            import sys
            tb = sys.exc_info()[2]
            ermsg = e.with_traceback(tb)
            print(u'日付フォーマットがおかしい{0}: {1}'.format(l, ermsg))
            # データ形式がおかしいのでロールバックさせて終了する
            return False
        else:
            # 正常に変換できた時の処理
            # DBにreplace into
            db.Replace('weekday', wdate = day, name = name)
    return True

def loading_weekday_info():
    db = DB(DBFILE)
    create_weekday_table(db)
    rslt = db.Execute('SELECT * FROM lastupdate').Col(None)
    if rslt is None or is_weekday_update(rslt[0]):
        if update_weekday_info(db, rslt):
            db.Commit()
        else:
            db.Rollback()

class main_frame(wx.Frame):
    def __init__(self, parent):
        wx.Frame.__init__(self, parent, wx.ID_ANY, u"dCalendar")

        # self.SetTransparent(200)
        panel_style = wx.TAB_TRAVERSAL
        panel_style |= wx.CLIP_CHILDREN
        panel_style |= wx.FULL_REPAINT_ON_RESIZE
        p = wx.Panel(self, -1, style = panel_style)

        main_sizer = wx.BoxSizer(wx.VERTICAL)

        # タイトル部分
        title = wx.BoxSizer(wx.HORIZONTAL)

        self.left_button = wx.Button(p, wx.ID_ANY, u"<",
                wx.DefaultPosition, wx.DefaultSize, 0)
        self.title_msg = wx.StaticText(p, wx.ID_ANY, u"",
            wx.DefaultPosition, wx.DefaultSize, wx.ALIGN_CENTER_HORIZONTAL)
        self.title_msg.SetFont(
            wx.Font(18, wx.FONTFAMILY_MODERN, wx.FONTSTYLE_NORMAL,
                wx.FONTWEIGHT_NORMAL, False, u"メイリオ"))
        self.title_msg.Wrap(-1)
        self.right_button = wx.Button(p, wx.ID_ANY, u">",
                wx.DefaultPosition, wx.DefaultSize, 0)

        title.Add(self.left_button, 1, wx.ALL, 5)
        title.Add(self.title_msg, 2, wx.ALL, 5)
        title.Add(self.right_button, 1, wx.ALL, 5)
        self.title_sizer = title
        self.left_button.Bind(wx.EVT_BUTTON, self.on_left_button)
        self.right_button.Bind(wx.EVT_BUTTON, self.on_right_button)
        self.title_msg.Bind(wx.EVT_LEFT_DOWN, self.on_today_button)

        main_sizer.Add(title, 1, wx.EXPAND, 1)

        # 曜日部分
        weekday = wx.BoxSizer(wx.HORIZONTAL)
        font = wx.Font(18, wx.FONTFAMILY_MODERN, wx.FONTSTYLE_NORMAL,
                wx.FONTWEIGHT_NORMAL, False, u"メイリオ")
        for msg, col in zip(WEEKDAY_MSG, WEEKDAY_COLOR):
            txt = wx.StaticText(p, wx.ID_ANY, msg,
                wx.DefaultPosition, wx.DefaultSize, wx.ALIGN_CENTER_HORIZONTAL)
            txt.Wrap(-1)
            txt.SetFont(font)
            if col:
                txt.SetForegroundColour(col)
            weekday.Add(txt, 1, wx.ALL, 0)

        main_sizer.Add(weekday, 1, wx.EXPAND, 1)
        self.weekday_sizer = weekday

        # 日付部分
        day = wx.GridSizer(MAX_WEEK, 7, 0, 0)
        self.day = []
        font = wx.Font(24, wx.FONTFAMILY_MODERN, wx.FONTSTYLE_NORMAL,
                wx.FONTWEIGHT_NORMAL, False, u"メイリオ")
        for _ in range(MAX_WEEK * 7):
            t = Button.GenButton(p, label="")
            t.SetFont(font)
            # t.Bind(wx.EVT_BUTTON, self.on_day_button)
            day.Add(t, 0, wx.EXPAND | wx.ALL, 0)
            self.day.append(t)

        main_sizer.Add(day, 6, wx.EXPAND | wx.ALL, 5)

        p.SetSizerAndFit(main_sizer)
        self.SetClientSize(p.GetSize())

        self.on_today_button(None)

    def view_calender(self, year, month):
        n = datetime.date(year, month, 1)
        self.title_msg.SetLabelText('{0:04d}年{1:02d}月'.format(year, month))
        self.title_sizer.Layout()
        # 1…月曜日,2…火曜日,…,7…日曜日
        weekday = n.isoweekday() % 7
        ndate = n - datetime.timedelta(days = weekday)
        db = DB(DBFILE)
        default_background_color = wx.SystemSettings.GetColour(
                wx.SYS_COLOUR_BTNFACE)
        for btn in self.day:
            nmonth = ndate.month
            nday = ndate.day
            nweek = ndate.isoweekday()
            weekday_msg = self.is_weekday(db, ndate)
            is_weekday = (weekday_msg is not False)
            flag = (nmonth == month)
            btn.SetLabelText('{0:2d}'.format(nday))
            if not flag:
                btn.SetBackgroundColour(wx.Colour(192, 192, 192))
            else:
                btn.SetBackgroundColour(default_background_color)

            if nweek == 7 or is_weekday:
                btn.SetForegroundColour(wx.Colour(255, 0, 0))
            elif nweek == 6:
                btn.SetForegroundColour(wx.Colour(0, 0, 255))
            else:
                btn.SetForegroundColour(wx.Colour(0, 0, 0))
            if is_weekday:
                # TODO: ツールチップのフォントを大きくしたい
                btn.SetToolTip(weekday_msg)
            else:
                btn.UnsetToolTip()

            btn.data = ndate

            ndate += datetime.timedelta(days = 1)
        self.Refresh()
        self.Update()

    def is_weekday(self, db, ndate):
        q = db.Execute('SELECT name FROM weekday WHERE wdate=?',
                ('{0:%Y-%m-%d}'.format(ndate))).Col(None)
        if q is None:
            return False
        return q[0]

    def change_month(self, vect):
        n = datetime.date(self.year, self.month, 1)
        n += relativedelta(months = vect)
        self.view_calender(n.year, n.month)
        self.year = n.year
        self.month = n.month

    def on_left_button(self, _):
        self.change_month(-1)

    def on_right_button(self, _):
        self.change_month(1)

    def on_today_button(self, _):
        today = datetime.date.today()
        self.view_calender(today.year, today.month)
        self.year = today.year
        self.month = today.month

    # TODO: ボタン入力でスケジュールを登録したい
    #def on_day_button(self, ev):
    #    btn = ev.GetEventObject()
    #    date = btn.data
    #    dlg = ScheduleDlg(self, date)
    #    dlg.Show()

    def __del__(self):
        pass

def main():
    '''dCalendar main'''
    loading_weekday_info()
    app = wx.App(False)
    frame = main_frame(None)
    frame.Show(True)
    app.MainLoop()

if __name__ == '__main__':
    main()


from PySide import QtGui, QtCore
#from PyQt4 import QtGui, QtCore


def set_dark_style(widget, top_widget=True, background_color = (79,79,79)):
#     if top_widget:
#         widget = widget.window()
#     
#     from PyQt4 import QtGui
#     pal = widget.palette()
#     pal.setColor(widget.backgroundRole(), QtGui.QColor(*background_color))
#     widget.setPalette(pal)    
#     
#     from qt_market import resource 
#     
#     icon_root = resource.get_root_path("icons").replace("\\", "/")
#     

    widget.setStyleSheet("""
QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical,QScrollBar::add-page:horizontal, QScrollBar::sub-page:horizontal {
   background: none;
}

QScrollBar:vertical {
     border: 0px solid grey;
     background-color: rgb(90,90,90); /* scroll background */
     width:16px;
     margin: 0px 0px 0px 0px;
}

QScrollBar::handle:vertical{
     background: rgb(120,120,120);
     border: 0px solid rgb(120,120,120);
     border-radius: 5px;    
     min-height: 40px;
}
QScrollBar::handle:vertical:hover{
     background: rgb(200,200,200);
}
QScrollBar::add-line:vertical{
    border: 0px solid grey;
    background: grey;
    height: 0px;
    subcontrol-position: bottom;
    subcontrol-origin: margin;
}

QScrollBar::sub-line:vertical{
    border: 0px solid grey;
    background: grey;
    height: 0px;
    subcontrol-position: top;
    subcontrol-origin: margin;
}


QScrollBar:horizontal {
    border: 0px solid grey;
    background-color: rgba(100,100,100); /* scroll background */
    height: 10px;
    margin: 0px 0px 0px 0px;
}
QScrollBar::handle:horizontal{
    background: rgb(120,120,120);
    border: 0px solid rgb(120,120,120);
    border-radius: 5px;  
    min-width: 50px;
}
QScrollBar::handle:horizontal:hover{
    background: rgb(200,200,200);
}
QScrollBar::add-line:horizontal{
    border: 0px solid grey;
    background: grey;
    width: 0px;
    subcontrol-position: right;
    subcontrol-origin: margin;
}

QScrollBar::sub-line:horizontal{
    border: 0px solid grey;
    background: grey;
    width: 0px;
    subcontrol-position: left;
    subcontrol-origin: margin;
}

QHeaderView::section, QTableCornerButton::section {
     background-color: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                                       stop:0 #4a4a4a, stop:1 #555555);                                 
     color: rgba(255,255,255,150);
     
     padding-left: 4px;
     border: 0px solid #6c6c6c;
     border-left: 1px solid rgb(59,59,59);
     border-bottom: 1px solid rgb(59,59,59);

     min-height:40px;     
     font: 20px;
}
QHeaderView::section::checked{
     background-color: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                                       stop:0 #4a4a4a, stop:1 #995555);                                 
     color: rgba(255,255,255,150);
}
QTableView, QTreeView {
     alternate-background-color: rgb(74,74,74);
     background-color: rgb(64,64,64);
     color: white;
     gridline-color: rgb(69,69,69);
}

QTableView:QLabel{
     color: white;
}

QTableView::item:selected {
     background-color: rgb(30,34,66);
     color:white;
} 
 
QTableView::item:selected:active {
     background-color: rgb(51,153,255);
     color:white;
}
 
QListView {
     alternate-background-color: rgb(79,79,79);
     background-color: rgb(79,79,79);
     color: white;
 }
QListView::item:selected {
     background-color: rgb(30,34,66);
     color:white;
 }
QListView::item:selected:active {
     background-color: rgb(51,153,255);
     color:white;
 }    
     
    """)
    return 




    widget.setStyleSheet(""" 

QMessageBox{
    background: rgb(80,80,80);
}

QPlainTextEdit, QComboBox, QLineEdit, QSpinBox{     
    color:white;
    background: rgba(0,0,0, 40);
    border: 1px solid #555555;    
    border-radius: 3px;
}


QSpinBox::up-button, QSpinBox::down-button{    
    border-width: 0px;
}

QGroupBox {
    color:white;
    border: 1px solid gray;
    border-radius: 5px;
    margin-top:3ex;  /* leave space at the top for the title */
}

QMenu {
    background-color: rgb(80,80,80); 
    border: 1px solid rgb(130,130,130);    
}



QMenu::item {
    padding: 2px 25px 2px 20px;
    border: 1px solid transparent; /* reserve space for selection border */
    color: white
}


QMenu::item:disabled {
    color: rgb(170,170,170);
}

QMenu::item:selected { /* when user selects item using mouse or keyboard */
    background-color: rgb(51,153,255);
}

QMenu::separator {
    height: 1px;
    background-color: rgb(110,110,110);
     
    margin-left: 0px;
    margin-right: 0px;
    
    margin-top: 5px;
    margin-bottom: 5px;
    
}

QMenu::indicator {
    margin-left: 5px;
    width: 10px;
    height: 10px;
    border-radius:3px;
}

QMenu::indicator:non-exclusive:unchecked, QMenu::indicator:exclusive:unchecked {
    background-color: transparent;
}

QMenu::indicator:non-exclusive:unchecked:selected {
    background-color: transparent;
}

QMenu::indicator:non-exclusive:checked, QMenu::indicator:exclusive:checked {
    background-color: qlineargradient(    x1:0, y1:0, x2:0, y2:1,
                                           stop:0 #aaeeff, stop: 0.7 #aabbbb, stop:1 #6699ee); 
}
 
QMenuBar {
    color: rgb(200,200,200);
    background-color: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                                      stop:0 rgb(75,75,75), stop:1 rgb(45,45,45) );
}

QMenuBar::item {
    background: transparent;
}

QMenuBar::item:selected { /* when selected using mouse or keyboard */
    color: white;
}

QStatusBar {    
    background: rgb(80,80,80);
    color:rgb(210,210,210);
}

QGroupBox::title {
    subcontrol-origin: margin;
    subcontrol-position: top center; /* position at the top center */
    padding: 0 10px;
}

QPlainTextEdit:disabled, QLineEdit:disabled, QComboBox:disabled{     
    color: rgba(255,255,255,80); 
    background: rgba(55,55,55,170);
    border: 1px solid rgba(77,77,77,170);    
    border-radius:3px;
}

QDialog {
    background: rgb(100,100,100);
}


QPushButton, QToolButton[autoRaise=false], QToolButton[autoRaise=true]:hover {
    border: 1px solid rgba(255,255,255,50);
    border-radius: 3px;
    padding: 5px;
}


QPushButton:disabled, QToolButton[autoRaise=false]:disabled{
    border: 1px solid rgba(255,255,255,30); 
    
    background-color: rgba(255,255,255,10);
    color: rgba(255,255,255,80);    
}


QPushButton:hover, QToolButton[autoRaise=true]:hover, QToolButton[autoRaise=false]:hover {
    background-color: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                                           stop:0 rgba(255,255,255,99), stop: 0.5 rgba(255,255,255,55),
                                           stop: 0.6 rgba(255,255,255,44), stop:1 rgba(255,255,255,66));
    color: rgba(255,255,255,200);
}


QToolButton[autoRaise=false], QPushButton{
    background-color: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                                           stop:0 rgba(255,255,255,55), stop: 0.5 rgba(255,255,255,50),
                                           stop: 0.6 rgba(255,255,255,50), stop:1 rgba(255,255,255,55));   
}

QToolButton, QPushButton{
    color: rgba(255,255,255,150);
}

QPushButton:hover:pressed, QComboBox:hover:pressed, QToolButton:hover:pressed  { 
    background-color: qlineargradient(    x1:0, y1:0, x2:0, y2:1,
                                           stop:0 #333333, stop: 0.3 #444444, stop:1 #555555); 
}

QPushButton:checked, QPushButton:flat:checked  { 
    background-color: qlineargradient(    x1:0, y1:0, x2:0, y2:1,
                                           stop:0 #aaeeff, stop: 0.7 #aabbbb, stop:1 #6699ee); 
}

QPushButton:flat { 
    border-radius: 0px;
    border:0px solid;
    background-color: rgba(0,0,0,0)
}


QComboBox::drop-down{
    border: 0px solid; 
    max-width: 1;   
} 

QComboBox::down-arrow{
    image:url(%(icon_root)s/down_arrow_combobox.png);
} 


QCheckBox {
    color: #aaaaaa;
}

QCheckBox::indicator {
    width: 10px;
    height: 10px;
    border: 1px solid #aaaaaa;
     border-radius:3px;
}

QCheckBox::indicator:hover {
    border: 1px solid #3366ff;    
}

QCheckBox::indicator:checked {
   border: 1px solid #888888;
   background-color: qlineargradient(    x1:0, y1:0, x2:0, y2:1,
                                          stop:0 #aaeeff, stop: 0.7 #5566aa, stop:1 #003355); 
}

QRadioButton {
    color: #aaaaaa;
}

QRadioButton::indicator {
    width: 10px;
    height: 10px;
    border: 1px solid #aaaaaa;
    border-radius:6px;
}

QRadioButton::indicator:hover {
    border: 1px solid #3366ff;    
}

QRadioButton::indicator:checked {
   border: 1px solid #888888;
   background-color: qlineargradient(    x1:0, y1:0, x2:0, y2:1,
                                          stop:0 #aaeeff, stop: 0.7 #5566aa, stop:1 #003355); 
}


QCheckBox, QRadioButton { 
    color:white;
}
QCheckBox:disabled, QRadioButton:disabled { 
    color:rgba(255,255,255,80); 
}

QLabel {     
     color:white;
}
QLabel:disabled { 
    color:rgba(255,255,255,80); 
}    

QTabWidget::pane { /* The tab widget frame */
   border: 1px solid rgb(150,150,150);
}

QTabWidget::tab-bar {
    left: 5px; /* move to the right by 5px */
}

QTabBar::tab {
    background-color: rgb(140,140,140);
    color: rgb(30,30,30);

    border-color: rgb(200,200,200); /* same as the pane color */

    /* border-top: 1px solid rgb(90,90,90); */
    border-left: 1px solid rgb(90,90,90);
   
    /* border-top-left-radius: 4px;
    border-top-right-radius: 4px; */

    min-width: 8ex;
    padding: 3px 12px 2px 12px;
    
}

QTabBar::tab:selected {
    border-left: 1px solid rgb(40,40,40);
    background-color: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                                      stop:0 lightgray, stop:1 darkgray);
    
}

QTextEdit {
    background-color: rgb(39,39,39);
    color: rgb(255,255,255);
    border: 0px solid #6c6c6c;
}


QTabBar::tab:hover {
    background-color: rgba(170,170,170);
}

QTabBar::tab:selected {
    border-color: #9B9B9B;
}

QTabBar::tab:!selected {
    /* margin-top: 3px; make non-selected tabs look smaller */
}

QSplitter::handle {
    background-color: rgba(0,0,0,0);
    image: url(images/splitter.png);
}

QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical,QScrollBar::add-page:horizontal, QScrollBar::sub-page:horizontal {
   background: none;
}

QScrollBar:vertical {
     border: 0px solid grey;
     background-color: rgb(90,90,90); /* scroll background */
     width:16px;
     margin: 0px 0px 0px 0px;
}

QScrollBar::handle:vertical{
     background: rgb(120,120,120);
     border: 0px solid rgb(120,120,120);
     border-radius: 5px;    
     min-height: 40px;
}
QScrollBar::handle:vertical:hover{
     background: rgb(200,200,200);
}
QScrollBar::add-line:vertical{
    border: 0px solid grey;
    background: grey;
    height: 0px;
    subcontrol-position: bottom;
    subcontrol-origin: margin;
}

QScrollBar::sub-line:vertical{
    border: 0px solid grey;
    background: grey;
    height: 0px;
    subcontrol-position: top;
    subcontrol-origin: margin;
}


QScrollBar:horizontal {
    border: 0px solid grey;
    background-color: rgba(100,100,100); /* scroll background */
    height: 10px;
    margin: 0px 0px 0px 0px;
}
QScrollBar::handle:horizontal{
    background: rgb(120,120,120);
    border: 0px solid rgb(120,120,120);
    border-radius: 5px;  
    min-width: 50px;
}
QScrollBar::handle:horizontal:hover{
    background: rgb(200,200,200);
}
QScrollBar::add-line:horizontal{
    border: 0px solid grey;
    background: grey;
    width: 0px;
    subcontrol-position: right;
    subcontrol-origin: margin;
}

QScrollBar::sub-line:horizontal{
    border: 0px solid grey;
    background: grey;
    width: 0px;
    subcontrol-position: left;
    subcontrol-origin: margin;
}

QSplitter::handle {
     background-color: rgba(0,0,0,0);
     image: url(images/splitter.png);
}

QHeaderView::section, QTableCornerButton::section {
     background-color: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                                       stop:0 #4a4a4a, stop:1 #555555);                                 
     color: rgba(255,255,255,150);
     
     padding-left: 4px;
     border: 0px solid #6c6c6c;
     border-left: 1px solid rgb(59,59,59);
     border-bottom: 1px solid rgb(59,59,59);

     min-height:25px;     
     font: 14px;
}

QWidget{
    font:13px;
}

CheckSetWidget{
    color: white;
    background-color: rgb(100,100,100);
}


QTableView, QTreeView {
     alternate-background-color: rgb(74,74,74);
     background-color: rgb(64,64,64);
     color: white;
     gridline-color: rgb(69,69,69);
}

QTableView:QLabel{
     color: white;
}

QTableView::item:selected {
     background-color: rgb(30,34,66);
     color:white;
} 
 
QTableView::item:selected:active {
     background-color: rgb(51,153,255);
     color:white;
}
 
QListView {
     alternate-background-color: rgb(79,79,79);
     background-color: rgb(79,79,79);
     color: white;
 }
QListView::item:selected {
     background-color: rgb(30,34,66);
     color:white;
 }
QListView::item:selected:active {
     background-color: rgb(51,153,255);
     color:white;
 }
    """ % vars() 
    )
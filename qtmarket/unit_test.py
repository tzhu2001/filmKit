import sys, os, time
from qtmarket import QtCore, QtGui
import qtmarket

from qtmarket.easy_table_widget import EasyTableWidget

qapp = QtGui.QApplication( sys.argv )

class VerCell(QtGui.QWidget):
    def __init__(self, parent=None, id=None, label=None, meta=None):
        '''
        @type parent: QtGui.QWidget
        @type id: int
        @type label: string
        @type meta: dict
        '''
        QtGui.QWidget.__init__(self,parent)
        self._id            = id
        self._label_text    = label
        self._meta          = meta
        self._image_ori     = None              # QtGui.QPixmap
        self._image_fit     = None              # QtGui.QPixmap
        self._image_mutex   = QtCore.QMutex()
        
        # widgets 
        self._label     = QtGui.QLabel(self)
        self._button    = QtGui.QPushButton(self)
        
        # set properties
        if self._label_text:
            self._button.setText(self._label_text)
        self._button.setFlat(True)
        
        # layout
        self._borderspace = 6
        l = QtGui.QVBoxLayout()
        l.addWidget(self._label)
        l.addWidget(self._button)
        l.setSpacing(self._borderspace/2)
        l.setContentsMargins(self._borderspace/2, self._borderspace/2, self._borderspace/2, self._borderspace/2)
        #l.setMargin( self._borderspace/2 )
        self.setLayout(l)
        
        
    def set_image(self, image, refresh=True):
        '''
        Set the image source
        @type image: QtGui.QPixmap, string
        '''
        if isinstance(image, basestring):
            image = QtGui.QPixmap(image)
            
        self._image_ori = image
        
        if refresh:
            self.refresh()

    def refresh(self):
        '''
        Refresh the icon
        '''
        image_ori = self._image_ori #: :type image_ori :QtGui.QPixmap
        if self._image_ori:
            image_fit = image_ori.scaledToWidth(
                                    self.size().width(), # - self._borderspace*2, 
                                    #self.size().height() - self._borderspace*2, 
                                    #aspectRatioMode  = QtCore.Qt.KeepAspectRatio, 
                                    #transformMode    = QtCore.Qt.SmoothTransformation
                                    mode    = QtCore.Qt.SmoothTransformation
                                    )
            
            self._label.setPixmap( image_fit )
            
            
    def resizeEvent (self, size):
        self.refresh()
            

class Test(QtGui.QWidget):
    def __init__(self):
        super(Test, self).__init__()
        button = QtGui.QPushButton('push me')

        table = EasyTableWidget()
        table.setVerticalScrollMode(QtGui.QAbstractItemView.ScrollPerPixel)
        #table.setShowGrid(False)
        table.setAlternatingRowColors(True)
        
        qtmarket.set_dark_style(table)
        
#         table.setStyleSheet('''
#                 QTableWidget::item
#                 {
#                   /*border: 1px solid green;*/
#                   
#                   padding: 20px;
#                   gridline-color: white;
#                 }
#                 QTableWidget::item:selected
#                 {
#                   background-color: lightgreen;
#                 }
#                 QTableWidget
#                 {
#                   /*border: 1px solid red;*/
#                   padding: 5px;
#                   spacing: 10px;
#                   gridline-color: white;
#                 }
#                         
#             ''')

        
        button.connect(button, QtCore.SIGNAL('clicked()'), self.scroll_table)

        v = QtGui.QVBoxLayout();
        v.addWidget(table)
        v.addWidget(button) 
        
        self.setLayout(v)
        self.table = table
        
        self._item_per_row = 4
        self._item_min_width = 200
        self._item_min_height = self._item_min_width * 0.75
        
        self._MAX_COLUMN = 10
        self.table.setColumnCount(self._MAX_COLUMN)
               
        self.table.setup_table( [ 'cell%s' % i for i in range( self._MAX_COLUMN ) ] )
        
        self.resizeEvent(None)
        self.table.setRowCount( 100 )
        
    
    def resizeEvent (self, size):
        item_per_row = max (1, self.width() / self._item_min_width )
        item_per_row = min (self._MAX_COLUMN, item_per_row )
        
#         visible_column_column = 0
#         for i in range(self._MAX_COLUMN):
#             if not self.table.isColumnHidden():
#                 visible_column_column += 1      
        
        vis_column_count = len ([ i for i in range(self._MAX_COLUMN) if not(self.table.isColumnHidden(i))])
        
        if item_per_row != vis_column_count:
            print 'rezie'
            
            for i in range(self._MAX_COLUMN):
                self.table.setColumnHidden(i, i>=item_per_row )
            
            self.table.clearContents()
            self._widget_list = [ VerCell (label="red_010_%04d" % d) for d in range (0, 260, 10) ] 
                    
            self.table.setRowCount( len(self._widget_list)/item_per_row + 1 )
            
            for row_i in range( self.table.rowCount()):
                self.table.setRowHeight(row_i, self._item_min_height )     
             
            for i, widget in enumerate(self._widget_list):
                self.table.setCellWidget (i/item_per_row, i%item_per_row, widget )
            
            vc = self.table.cellWidget(0,0)
            vc.set_image(r'C:\Users\Tommy\Pictures\hero\spidey.png')
            
            
#             #::type label: QtGui.QLabel
#             label = self.table.cellWidget(0,0)       
#             label.setText("Hulk Must Smash")
#             
            ef = QtGui.QGraphicsOpacityEffect(self)
            vc.setGraphicsEffect(ef)
#             vc.setPixmap( QtGui.QPixmap() )
            
            anim = QtCore.QPropertyAnimation (parent=self)
            anim.setTargetObject( ef )
            anim.setPropertyName('opacity')
            anim.setDuration(3000)
            anim.setEasingCurve(QtCore.QEasingCurve.OutExpo); 
            anim.setStartValue(0)
            anim.setEndValue(0.8)
            anim.start()
            
            #l.setGraphicsEffect()
        
    
        
    def scroll_table(self):

        slider = self.table.verticalScrollBar()
         
        vpos = self.table.rowViewportPosition(9)
         
        scroll_anim = QtCore.QPropertyAnimation(parent=self) #slider, 'value')
        scroll_anim.setTargetObject(slider)
        scroll_anim.setPropertyName('value')
        scroll_anim.setDuration(1000)
        scroll_anim.setStartValue( slider.value()  )
        scroll_anim.setEndValue( vpos + slider.value() )
        scroll_anim.setEasingCurve(QtCore.QEasingCurve.OutExpo);
        scroll_anim.start()


main = Test()


main.resize(QtCore.QSize(1000,500))
main.show()
sys.exit( qapp.exec_() )
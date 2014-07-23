'''
Easy Table widget adds to the existing QTableWidget by helping with setup of the table, entering data.

@@@ TODO @@@: write more docs
'''

from qtmarket import QtGui, QtCore
import os

# from qt_market.status_widget import StatusLabel, StatusWidget

check_icon = None
def set_cool_checkbox_style(button, size=None):
    '''
    Customize the check box.
    '''
    from PyQt4 import QtCore, QtGui
    from qt_market import resource
    
    global check_icon
    if not check_icon:
        check_icon = QtGui.QIcon()
        check_icon.addPixmap(QtGui.QPixmap(resource.get_root_path("icons", "check_2.png")), QtGui.QIcon.Active, QtGui.QIcon.On)
        check_icon.addPixmap(QtGui.QPixmap(resource.get_root_path("icons", "uncheck_2.png")), QtGui.QIcon.Active, QtGui.QIcon.Off)
    
    if size:
        button.setMinimumSize(size)
        button.setMaximumSize(size)        
        button.setIconSize(QtCore.QSize(16, 16))     
        
    button.setText("")
    button.setCheckable(True)
    button.setFlat(True)
    button.setIcon(check_icon)
     
     
        
class EasyTableWidget(QtGui.QTableWidget): 
    def __init__(self, default_width=60, parent=None):
        QtGui.QTableWidget.__init__(self, parent)
        
        # set the table properties
        self._default_header_width = default_width
        self._default_icon_size = 60
                
        self.setAlternatingRowColors(True)
        self.setIconSize(QtCore.QSize(self._default_icon_size, self._default_icon_size))
        
        self.verticalHeader().setVisible(False)
        
        self.setFrameShape(QtGui.QFrame.NoFrame)
        self.horizontalHeader().setMinimumSectionSize(self._default_header_width)
        
        self._ignore_playlist_selection_update = False
        


    def updateGeometries(self):
        '''
        Override the update Geometry code to override the corner button to disable select all cells. 
        '''
        # Call the updateGeometries function defined by QTableView first
        QtGui.QTableWidget.updateGeometries(self)
        # Find the corner widget and disable it!
        self.findChild(QtGui.QAbstractButton).setEnabled(False)
        
        
    def clear_and_reset(self):
        '''
        Clear the and reset the table to clean slate with the header
        '''
        self.clearContents ()
        self.setRowCount(0)
        
        self.setup_table(                         
                         self._header_name,
                         self._header_label,
                         self._header_width,
                         self._header_type,
                         self._trigger,
                         self._index_columns,
                         self._tool_tip,
                         )
        
        
    def setup_table(self, name, label={}, width={}, _type={}, trigger=[], index=[], tool_tip={}):
        '''
        Setup the table with 
        @param name list of names for the column
        @param label column label, key is the column name
        @param width column width, key is the column name  
        @param _type column _type, key is the column name, will dictate the control use in the each cell in column.
        @param trigger column trigger, not used
        @param index
        @param tool_tip, the key is the column name
        '''
        self._header_name   = name
        self._header_label  = label        
        self._header_width  = width
        self._header_type   = _type
        self._trigger       = trigger
        self._index_columns = index
        self._tool_tip      = tool_tip
        
        
        self._index_columns_hash = {}
                    
        col_index = 0
        
        self.setColumnCount( len(self._header_name) )
        if self._header_width and len(self._header_width.keys())==0:
            self._header_width[self._header_name[-1]] = -99
        
        for name in self._header_name:
            header = QtGui.QTableWidgetItem();
             
            header.setText( self._header_label[name] if self._header_label.has_key(name) else name )
            
            if name in tool_tip:
                header.setToolTip(tool_tip[name])
            
            self.setHorizontalHeaderItem(col_index, header)
            
            if not self._header_width: # everything equal and stretch                
                self.horizontalHeader().setResizeMode( col_index, QtGui.QHeaderView.Stretch )
                
            else:
                if name in self._header_width:
                    if self._header_width[name]==-9:
                        self.setColumnHidden(col_index, True)
                        
                    elif self._header_width[name]==-99:
                        # do something
                        self.horizontalHeader().setResizeMode( col_index, QtGui.QHeaderView.Stretch )
                    else:
                        self.setColumnWidth( col_index, self._header_width[name] )
                        
                else:
                    self.setColumnWidth( col_index, self._default_header_width)
            
            col_index+=1
            
            
        self.verticalHeader().setVisible(True)
        
        item = QtGui.QTableWidgetItem()
        item.setText('hello')
        self.setVerticalHeaderItem(0, item)        
            
            
    def move_selection_up(self, direction=1):
        """
        Move the selected rows up once.
        If direction is -1, then it will move the selected row down by one.
        """
        row_selection = [ index.row() for index in self.selectionModel().selectedRows() ]
        row_selection.sort(reverse = False if direction==1 else True)
        
        if len(row_selection)==0: 
            return 
        
        if direction==1 and row_selection[0]==0: # highest selection is top row
            return
        
        elif direction==-1 and row_selection[0]== self.rowCount() -1:
            return 
        
        self._ignore_playlist_selection_update = True
        self.clearSelection()
        for index in row_selection:
            prev_row = self._take_row(index-direction)
            move_row = self._take_row(index)
            self._set_row(index-direction, move_row)
            self._set_row(index, prev_row)
        
            self.select_row(index-direction)
        
        self._ignore_playlist_selection_update = False
            
            
    def move_selection_down(self):
        '''
        Move the selecte rown down.
        '''
        self.move_selection_up(direction=-1)
        
    
    def _take_row(self, row_index):
        """
        Take the items out of a row and return them.  Used in conjuction with set_row to move row up and down
        """
        return self.get_row_data(   row_index, flg_include_control_properties=True), \
                                    [ self.takeItem(row_index, c) for c in xrange(self.columnCount()) ]
                                    
    
    def _set_row(self, row_index, row_data_tuple):
        """
        Set the row of row index row_index to the data in the row_data_tuple
        @param row_index
        @param row_data_tuple 
        """
        data_hash, row_items = row_data_tuple
        for col_index in xrange(len(row_items)):
            self.setItem(row_index, col_index, row_items[col_index] )     
        
        self.update_row(row_index, data_hash, flg_include_control_properties=True )
    
    
    def select_row(self, row_index, mode=QtGui.QItemSelectionModel.Select, scroll_to_selection=False):
        '''
        @param row_index Given the row index, select the row, with option to scroll to selection
        @param scroll_to_selection will scroll to the selection  
        '''
        # some weirdness where only one cell will be selected if use ClearAndSelect, hence do my own clear and select
        if mode==QtGui.QItemSelectionModel.ClearAndSelect:   
            self.selectionModel().clear()
            mode = QtGui.QItemSelectionModel.Select
            
        for k in xrange(self.columnCount()):
            self.selectionModel().select(self.model().index(row_index,k), mode) 
        
        if scroll_to_selection:
            self.scroll_to_row(row_index)
    
    
    def set_column_visble(self, header_name, visible=True):
        '''
        Set the visbility for a column
        '''
        self.setColumnHidden( self._header_name.index(header_name), not visible )
        
        

    def scroll_to_row(self, row_index, scroll_mode= QtGui.QAbstractItemView.EnsureVisible):
        '''
        @param row_index scroll to the row
        @param scroll_mode default is ensure row is visible, other QtCore.Qt.PositionAtTop etc.
        '''
        # find the a item that is visible
        vibible_col = [k for k in range(self.columnCount()) if not self.isColumnHidden(k) ]
        
        if vibible_col:            
            row_index = self.visualRow (row_index)
            item = self.item(row_index, vibible_col[0] )
            self.scrollToItem( item, scroll_mode)

    
    def append_row(self, data_hash, row_index=None, row_height=None, insert_new_row=True):
        if row_index==None:
            row_index = self.rowCount()
            
        self.insert_row(row_index, data_hash, row_height, insert_new_row)
    
    
    def insert_row(self, row_index=0, data_hash={}, row_height=None, insert_new_row=True):
        """
        Insert the a new row at into the table with the selected row_index
        
        @param: no new row is inserted in the database, rather the controls are create for that the new row.
        
        Args:
            row_index: the index of the row being query upon  
                    
            data_hash: A dictionary of data with the information.  Note: table doesn't need to be complete.
                example:                
                {
                    "source":       "q030s_s0400",
                    "artist":       "h.jordan",
                    "dept":         "rlo",
                    "frame_in":     "1000",
                    "frame_out":    "1321",
                    "version":      "v002",
                    "thumb":         "c:\Users\t.zhu\workspace\proto_tzhu\review_tool\resource\q030s0500.jpg" ),
                }
        
        """      
        
        ori_sort_setting = self.isSortingEnabled()
        
        self.setSortingEnabled(False) # if sorting is not set to false, as the data is enter, the empty row will sort and result
        if insert_new_row:
            self.insertRow(row_index)
        
        if row_height:
            self.setRowHeight(row_index, row_height)             
        
        control_hash = {}
        # create the controls
        for name in self._header_name:        
            col_index = self._header_name.index(name)
                
            if name in self._header_type and self._header_type[name]=="checkbox":
                cntl = QtGui.QPushButton(self)
                set_cool_checkbox_style(cntl)
                 
                self.setCellWidget(row_index, col_index, cntl)                
                
            elif name in self._header_type and self._header_type[name]=="status_label":                                
                cntl = StatusLabel(parent = self)
                self.setCellWidget(row_index, col_index, cntl )     
                
            elif name in self._header_type and self._header_type[name]=="status_widget":                
                cntl = StatusWidget(parent=self)
                self.setCellWidget(row_index, col_index, cntl)    
                
            elif name in self._header_type and self._header_type[name]=="frame_spinbox":
                from qt_market.frame_spinbox_widget import FrameSpinBoxWidget
                cntl = FrameSpinBoxWidget(parent=self)                     
                self.setCellWidget(row_index, col_index, cntl)
                
            elif name in self._header_type and self._header_type[name]=="dependency":
                from qt_market.dependency_cell_widget import DependencyCellWidget
                cntl = DependencyCellWidget(parent=self)                     
                self.setCellWidget(row_index, col_index, cntl)
                
            elif name in self._header_type and self._header_type[name]=="version":
                from qt_market.version_cell_widget import VersionCellWidget
                cntl = VersionCellWidget(parent=self)                     
                self.setCellWidget(row_index, col_index, cntl)
                
            elif name in self._header_type and self._header_type[name]=="version_button":
                from qt_market.version_cell_widget import VersionCellButtonWidget
                cntl = VersionCellButtonWidget(parent=self)                     
                self.setCellWidget(row_index, col_index, cntl)
                
            elif name in self._header_type and self._header_type[name]=="checkset":
                from qt_market.check_set_cell_widget import CheckSetCellWidget
                cntl = CheckSetCellWidget(parent=self)                     
                self.setCellWidget(row_index, col_index, cntl)
                
            else:                        
                cntl = QtGui.QTableWidgetItem()    
                self.setItem ( row_index, col_index, cntl )
        
            control_hash[name] = cntl            
                
        self.update_row(row_index, data_hash)
                
        self.setSortingEnabled(ori_sort_setting)
        
        return control_hash
    

    def update_row(self, row_index=0, data_hash={}, flg_include_control_properties=False):
        """
        Update the data in the row
        """        
        for name in data_hash:
            # skip updating data not in table
            if name not in self._header_name:
                if name not in ["_row_index"]: 
                    print "This row name is not handle by update, data is discard: %s" % name
                continue
            
            # skip if the data is none
            if data_hash[name]==None:
                continue
            
            # index the row that requires indexing
            if name in self._index_columns:
                if name not in self._index_columns_hash:
                    self._index_columns_hash[name] = {}
                
                self._index_columns_hash[name][data_hash[name]] = row_index
            
            col_index   = self._header_name.index(name)
            cell_widget = self.cellWidget(row_index, col_index)
            
            if name in self._header_type and self._header_type[name]=="icon":
                icon_path = data_hash[name]
                                                          
                if type(icon_path) in (str, unicode ) and os.path.isfile( icon_path ):
                    icon = QtGui.QIcon()
                    pixmap  = QtGui.QPixmap(icon_path)
                      
                    icon.addPixmap(pixmap , QtGui.QIcon.Normal, QtGui.QIcon.Off )                                                   
                    self.item(row_index, col_index).setIcon(icon)
                    self.item(row_index, col_index).setData(9999, QtCore.QVariant(QtCore.QString(icon_path)))
                
                elif type(icon_path)==QtGui.QIcon:
                    self.item(row_index, col_index).setIcon( data_hash[name] )
                    self.item(row_index, col_index).setData(9999, QtCore.QVariant(True))
                     
                elif type(icon_path)==QtGui.QPixmap:                    
                    icon = QtGui.QIcon()  
                    icon.addPixmap( icon_path, QtGui.QIcon.Normal, QtGui.QIcon.Off )                                                   
                    self.item(row_index, col_index).setIcon(icon)
                                        
                else:
                    self.item(row_index, col_index).setData(9999, QtCore.QVariant(QtCore.QString(icon_path)))
                    
                    print "Thumb not found in path '%s'." % data_hash[name]
        
            elif name in self._header_type and self._header_type[name]=="int":
                self.item(row_index, col_index).setText(str(data_hash[name]))
                self.item(row_index, col_index).setFlags( QtCore.Qt.ItemIsSelectable|QtCore.Qt.ItemIsEnabled)#|QtCore.Qt.ItemIsDragEnabled|QtCore.Qt.ItemIsDropEnabled )
                
            elif name in self._header_type and self._header_type[name].startswith("v%"):          
                if ( type(data_hash[name])==int or data_hash[name].isdigit() ):                    
                    self.item(row_index, col_index).setText( self._header_type[name] % int(data_hash[name]) )
                                       
            elif name in self._header_type and self._header_type[name]=="checkbox":
                
                cell_widget.setChecked(True if (data_hash[name]=="True" or data_hash[name]==True) else False)
                  
            elif name in self._header_type and self._header_type[name]=="frame_spinbox":
                cell_widget.set_value(data_hash[name], flg_include_control_properties)

            elif name in self._header_type and self._header_type[name] in ("status_label", "status_widget"):                
                cell_widget.set_status(data_hash[name])
                                                   
            elif cell_widget and hasattr(cell_widget, "set_value"):
                cell_widget.set_value(data_hash[name])
                
            elif cell_widget and hasattr(cell_widget, "set_data"):
                cell_widget.set_data(data_hash[name])
            
            else:                  
                #self.item(row_index, col_index).setFlags( QtCore.Qt.ItemIsSelectable|QtCore.Qt.ItemIsEnabled|QtCore.Qt.ItemIsDragEnabled|QtCore.Qt.ItemIsDropEnabled )
                self.item(row_index, col_index).setText(str(data_hash[name]))
                
                tooltip = data_hash[name]
                
                if name in self._tool_tip:
                    tooltip = self._tool_tip[name]
                          
                #self.item(row_index, col_index).setData(QtCore.Qt.ToolTipRole, QtCore.QVariant( QtCore.QString( str(tooltip)) ) )      
                self.item(row_index, col_index).setData(QtCore.Qt.ToolTipRole, tooltip ) 
                    
                    
    def remove_selected_row(self):
        select_index_list = [r.row() for r in self.selectionModel().selectedRows()]
        select_index_list.sort()
        select_index_list.reverse()
        
        # build list of all the shots to removed
        for i in select_index_list:
            self.removeRow(i)
                                                        
                
#    def get_cell_widget(self, row_index, col_name):
#        return self.cellWidget(row_index, self._header_name.index(col_name))


    def get_cell_widget(self, row_index, col_name, include_item_wiget=False ):
        """
        if include_item_wiget, and there is not cell widget assigned, it will return the default tableWidgetItem.
        """        
        cellwidget = self.cellWidget(row_index, self._header_name.index(col_name))
        
        if cellwidget:
            return cellwidget
        elif include_item_wiget:
            return self.item(row_index, self._header_name.index(col_name)) 
        
                
        
    def get_cell_item(self, row_index, col_name):
        """
        similar to get_cell_widget, except return the table item if no widget
        """
        cell_widget = self.get_cell_widget(row_index, col_name)
        
        if cell_widget:            
            return cell_widget
        
        else:
            return self.item(row_index, self._header_name.index(col_name))


    def set_cell_widget(self, row_index, col_name, widget):
        '''
        @param row_index
        @param col_name
        @param widget
        set the widget to the cell with row_index and column name.
        '''
        self.setCellWidget(row_index, self._header_name.index(col_name), widget)
    
    
    def get_selected_rows(self, visible_only=True):
        selected_row_index_list = [ r.row()  for r in self.selectionModel().selectedRows() ]
        
        if visible_only:
            selected_row_index_list = [ i for i in selected_row_index_list if not self.isRowHidden(self.visualRow(i))]
                                               
        rows = [ self.get_row_data( r )  for r in selected_row_index_list ]
        rows.sort(lambda x,y: cmp(x['_row_index'], y['_row_index']) )
        
        return rows
    
        
    def get_selected_cell(self, visible_column_only=False):
        """
        for the selected cells, return the row and the column information, and the row data 
        return list of data tuples (row_data, col_name)
        """
        selected_cell_meta = [] 
        
        for index in self.selectionModel().selectedIndexes():            
            row_data = self.get_row_data(index.row())
            col_name = self._header_name[ index.column() ]
            
            # check if column
            if visible_column_only and self.isColumnHidden(index.column()):
                continue                
             
            selected_cell_meta.append( {
                                        "row_data":     row_data,
                                        "col_name":     col_name,
                                        "cell_widget":  self.cellWidget(index.row(), index.column()),
                                        "cell_item":    self.item(index.row(), index.column()), 
                                        "row_index":    index.row(),
                                        "column_index": index.column(), 
                                        } )
        
        return selected_cell_meta 
    
    
    def select_cells(self, cell_list, mode=QtGui.QItemSelectionModel.Select):        
        for cell in cell_list:
            if type(cell)==dict:
                self.selectionModel().select(self.model().index(cell["row_index"], cell["column_index"]), mode)
            else:          
                self.selectionModel().select(self.model().index(cell["row_index"], cell["column_index"]), mode)
    
    
    def get_all_data(self, keys=None):                
        return [ self.get_row_data(i, keys=keys) for i in xrange(self.rowCount())]
    
    
    def insert_all_data(self, data_list):
        index = 0
        for data in data_list:
            self.insert_row(index, data)
            index += 1
            
            
    def find_row_data(self, key_name, key_value):
        """
        return the row data matching the criteria
        ie: key_name = "shot_code", key_value = "q100_s0010"
        """

        if key_name in self._index_columns:            
            row_index = self._index_columns_hash[key_name][key_value]            
            return [ self.get_row_data(row_index) ]
         
        else:
            return [k for k in self.get_all_data() if key_name in k and k[key_name]==key_value ]
        

    def find_row_index(self, key_name, key_value):
        """
        @return the row index matching the criteria        
        """
        matches     = [ d for d in self.get_all_data(keys=[key_name]) if d[key_name]==key_value ]
        row_indices = [ d['_row_index'] for d in matches ]
        
        return row_indices 
         
                
        
    def filter_by_text(self, text_filter, ignore_case=True): 
        '''
        Only show the rows with the text in text_filter.
        @param text_filter the string to search for.
        @param ignore_case default is true
        '''        
        for i in range( self.rowCount() ):
            
            row_data = str( self.get_row_data(i) )
            
            if ignore_case: 
                row_data = str( row_data ).lower()
                text_filter = text_filter.strip()
            
            if text_filter in row_data:
                self.showRow(i)
                
            else:
                self.hideRow(i)
            

        
        
    def get_row_data(self, row_index, flg_include_control_properties=False, keys=None):
        """
        @param keys If this is specified, then only the data in the key list is returned.
        For a table widget need to implement the drag move event
        
        Args:
            row_index: the index of the row being query upon  
        
        Returns:
            A dictionary of data with the information. It always contain the current row index
            example:
            
            {
                "source":       "q030s_s0400",
                "artist":       "h.jordan",
                "dept":         "rlo",
                "frame_in":     "1000",
                "frame_out":    "1321",
                "version":      "v002",
                "thumb":        "c:\Users\t.zhu\workspace\proto_tzhu\review_tool\resource\q030s0500.jpg" ),
                "_row_index":   1 
            }
        
        """ 
        data_hash = {}       
        
        if type(keys) in (str, unicode): # user pass in one key, rather than a list of keys
            keys = [keys]
            
        if not keys:
            keys = self._header_name

        
        for name in keys:
            # TODO: check the type and cast the data appropriately 
            # if name in self._header_type:            
            data_hash[name] = None
            cell_widget     = self.get_cell_widget(row_index, name) # if any
            
            if name in self._header_type and self._header_type[name]=="checkbox":
                data_hash[name] = cell_widget.isChecked() if cell_widget else None
                
            elif name in self._header_type and self._header_type[name]=="frame_spinbox":
                data_hash[name] = cell_widget.get_value(flg_include_control_properties) if cell_widget else None                
            
            elif name in self._header_type and self._header_type[name]=="int":
                item = self.item( row_index, self._header_name.index(name) )
                
                if item and str(item.text())!="":                                 
                    data_hash[name] = int( item.text() )
                    
            elif name in self._header_type and self._header_type[name].startswith("v%"):
                item = self.item( row_index, self._header_name.index(name) )  
                
                if item and str(item.text())!="":              
                    data_hash[name] =  int( str( item.text() )[1:] )         
                    
            elif name in self._header_type and self._header_type[name]=="icon":
                item = self.item( row_index, self._header_name.index(name) )
                
                if item and item.data(9999):                    
                    data_hash[name] =  str(item.data(9999).toString())
                else:
                    data_hash[name] =  None
            
            elif name in self._header_type and self._header_type[name] in ("version", "version_button"):
                data_hash[name] = cell_widget.get_value() if cell_widget else None
                
                    
            elif cell_widget and hasattr( cell_widget, "get_data" ):
                data_hash[name] =  cell_widget.get_data() if cell_widget else None    

            elif cell_widget and hasattr( cell_widget, "get_value" ):
                data_hash[name] =  cell_widget.get_value() if cell_widget else None
                
            else:
                item = self.item( row_index, self._header_name.index(name) )
                if item:                 
                    data_hash[name] = str( item.text() )
        
        data_hash["_row_index"] = row_index
        return data_hash

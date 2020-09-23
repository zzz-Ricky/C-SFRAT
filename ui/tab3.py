from PyQt5.QtWidgets import QWidget, QHBoxLayout, QLabel, QGridLayout, \
                            QTableWidget, QTableWidgetItem, QAbstractScrollArea, \
                            QSpinBox, QSpacerItem, QSizePolicy, QHeaderView, QVBoxLayout, \
                            QListWidget, QAbstractItemView, QGroupBox, QListWidgetItem, \
                            QFrame, QTableView
from PyQt5.QtCore import pyqtSignal, QSortFilterProxyModel
from PyQt5.QtGui import QFont

import pandas as pd

# For exporting table to csv
import csv

# Local imports
from core.comparison import Comparison
from core.dataClass import PandasModel


class Tab3(QWidget):
    """Contains all widgets displayed on tab 3.

    Attributes:
        sideMenu: SideMenu object holding tab 3 widgets and their signals.
        table: QTableWidget that contains the goodness-of-fit measures for each
            calculated model/metric combination.
        font: QFont object that is formatted bold. Used to set text bold for
            cells containing the highest ranked combinations, according to the
            weighting of each measure.
    """

    def __init__(self):
        """Initializes tab 3 UI elements."""
        super().__init__()
        self._setupTab3()

    def addResultsToTable_old(self, results):
        """Perfoms comparison calculations, adds goodness of fit results to table.

        Args:
            results: A dict containing the model objects as values, indexed by
                the name of the model/metric combination. The model objects
                contain the goodness of fit measures as properties.
        """
        # numResults = len(results)
        self.table.setSortingEnabled(False) # disable sorting while editing contents
        self.table.clear()
        self.table.setHorizontalHeaderLabels(["Model Name", "Covariates", "Log-Likelihood", "AIC", "BIC",
                                              "SSE", "Model ranking", "Weighted model ranking"])
                                              #"Weighted selection (mean)", "Weighted selection (median)"])
        self.table.setRowCount(len(results))    # set row count to include all model results, 
                                                # even if not converged
        i = 0   # number of converged models

        self.sideMenu.comparison.goodnessOfFit(results, self.sideMenu)

        for key, model in results.items():
            if model.converged:
                self.table.setItem(i, 0, QTableWidgetItem(model.shortName))
                self.table.setItem(i, 1, QTableWidgetItem(model.metricString))
                self.table.setItem(i, 2, QTableWidgetItem("{0:.3f}".format(model.llfVal)))
                self.table.setItem(i, 3, QTableWidgetItem("{0:.3f}".format(model.aicVal)))
                self.table.setItem(i, 4, QTableWidgetItem("{0:.3f}".format(model.bicVal)))
                self.table.setItem(i, 5, QTableWidgetItem("{0:.3f}".format(model.sseVal)))
                try:
                    self.table.setItem(i, 6, QTableWidgetItem("{0:.3f}".format(self.sideMenu.comparison.meanOutUniform[i])))
                    self.table.setItem(i, 7, QTableWidgetItem("{0:.3f}".format(self.sideMenu.comparison.meanOut[i])))
                except TypeError:
                    # if no models converge, meanOut and meanOutUniform are set to None
                    # don't add item to table if type is None
                    pass
                i += 1
        self.table.setRowCount(i)   # set row count to only include converged models
        self.table.resizeColumnsToContents()    # resize column width after table is edited
        self.table.setSortingEnabled(True)      # re-enable sorting after table is edited

        try:
            self.table.item(self.sideMenu.comparison.bestMeanUniform, 6).setFont(self.font)
            self.table.item(self.sideMenu.comparison.bestMean, 7).setFont(self.font)
        except TypeError:
            # if no models converge, bestMean and bestMeanUniform will be None type
            # do not set cells to bold if they are None
            pass

    def addResultsToTable(self, results):
        # for key, model in results.items():
        #     row = [[model.shortName, model.metricString, model.llfVal, model.aicVal, model.bicVal, model.sseVal, 0, 0]]
        #     row_df = pd.DataFrame(row, columns=["Model Name", "Covariates", "Log-Likelihood", "AIC", "BIC", "SSE",
        #         "Model ranking", "Weighted model ranking"])
        #     print(hex(id(self.dataframe)))
        #     print(self.table.model())
        #     self.dataframe = self.dataframe.append(row_df, ignore_index=True)
        #     print(hex(id(self.dataframe)))
        #     print(self.table.model())
        #     print(self.dataframe)

        self.sideMenu.comparison.goodnessOfFit(results, self.sideMenu)

        rows = []
        row_index = 0
        for key, model in results.items():
            row = [model.shortName, model.metricString, model.llfVal, model.aicVal,
                model.bicVal, model.sseVal, self.sideMenu.comparison.meanOutUniform[row_index],
                self.sideMenu.comparison.meanOut[row_index]]
            rows.append(row)
            row_index += 1
        row_df = pd.DataFrame(rows, columns=["Model Name", "Covariates", "Log-Likelihood", "AIC", "BIC", "SSE",
            "Model ranking", "Weighted model ranking"])
        # self.dataframe.loc[self.dataframe.index.max() + 1] = row
        self.tableModel.setAllData(row_df)


        # import csv

        # with open('NASA_covariate.csv', 'w') as fileOutput:
        #     writer = csv.writer(fileOutput)
        #     writer.writerows(rows)



        self.table.model().layoutChanged.emit()
        # self.table.model().update()
        # self.table.update()

    def addRow(self, model, results):
        # new row inserted at end of table, after last row
        rowCount = self.table.rowCount()

        self.table.setItem(rowCount, 0, QTableWidgetItem(model.shortName))
        self.table.setItem(rowCount, 1, QTableWidgetItem(model.metricString))
        self.table.setItem(rowCount, 2, QTableWidgetItem("{0:.3f}".format(model.llfVal)))
        self.table.setItem(rowCount, 3, QTableWidgetItem("{0:.3f}".format(model.aicVal)))
        self.table.setItem(rowCount, 4, QTableWidgetItem("{0:.3f}".format(model.bicVal)))
        self.table.setItem(rowCount, 5, QTableWidgetItem("{0:.3f}".format(model.sseVal)))
        try:
            self.table.setItem(rowCount, 6,QTableWidgetItem("{0:.3f}".format(self.sideMenu.comparison.meanOutUniformDict[model.combinationName])))
            self.table.setItem(rowCount, 7, QTableWidgetItem("{0:.3f}".format(self.sideMenu.comparison.meanOutDict[model.combinationName])))
        except TypeError:
            # if no models converge, meanOut and meanOutUniform are set to None
            # don't add item to table if type is None
            pass


    # def addRow(self, model, results):
    #     row = [model.shortName, model.metricString, model.llfVal, model.aicVal, model.bicVal, model.sseVal]
    #     self.dataframe.append(row)

    #     self.table.model().layoutChanged.emit()

    def removeRow(self, model):
        # iterate over all rows, linear search
        rowCount = self.table.rowCount()

        for row in range(rowCount):
            modelName = self.table.item(row, 0)
            # first check if model name is the same as in table
            if modelName == model.shortName:
                covariates = self.table.item(row, 1)
                # finally, check if metric names are the same
                if covariates == model.metricNames:
                    # if both are the same, then this is the row to be deleted
                    self.table.removeRow(row)

    def _setupTab3(self):
        """Creates tab 3 widgets and adds them to layout."""
        mainLayout = QHBoxLayout()       # main layout
        self.sideMenu = SideMenu3()
        self.table = self._setupTable()
        self.font = QFont()     # allows table cells to be bold
        self.font.setBold(True)
        mainLayout.addLayout(self.sideMenu, 15)
        mainLayout.addWidget(self.table, 85)
        self.setLayout(mainLayout)

    def _setupTable_old(self):
        """Creates table widget with proper headers.

        Returns:
            A QTableWidget with specified column headers.
        """
        table = QTableWidget()
        table.setEditTriggers(QTableWidget.NoEditTriggers)     # make cells unable to be edited
        table.setSizeAdjustPolicy(QAbstractScrollArea.AdjustToContents)
                                                                    # column width fit to contents
        table.setRowCount(1)
        columnLabels = ["Model Name", "Covariates", "Log-Likelihood", "AIC", "BIC",
                        "SSE", "Model ranking", "Weighted model ranking"]
        table.setColumnCount(len(columnLabels))
        table.setHorizontalHeaderLabels(columnLabels)
        table.move(0, 0)

        header = table.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.ResizeToContents)
        # provides bottom border for header
        stylesheet = "::section{Background-color:rgb(250,250,250);}"
        header.setStyleSheet(stylesheet)

        return table

    def _setupTable(self):

        self.dataframe = pd.DataFrame(columns=["Model Name", "Covariates", "Log-Likelihood", "AIC", "BIC",
                                              "SSE", "Model ranking", "Weighted model ranking"])
        self.tableModel = PandasModel(self.dataframe)
        # self.proxyModel = QSortFilterProxyModel()
        # self.proxyModel.setSourceModel(self.tableModel)

        table = QTableView()
        # table.setModel(self.proxyModel)
        table.setModel(self.tableModel)
        table.setEditTriggers(QTableWidget.NoEditTriggers)     # make cells unable to be edited
        table.setSizeAdjustPolicy(QAbstractScrollArea.AdjustToContents)
                                                                    # column width fit to contents
        header = table.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.ResizeToContents)
        # provides bottom border for header
        stylesheet = "::section{Background-color:rgb(250,250,250);}"
        header.setStyleSheet(stylesheet)
        return table

    def exportTable(self):
        """
        Export table to csv
        """
        # TODO:
        # permission error (if file is open, etc.)
        # export other tables
        # export to excel?
        # stream writing vs line by line (?), not sure which is better/faster

        # https://stackoverflow.com/questions/57419547/struggling-to-export-csv-data-from-qtablewidget
        # https://stackoverflow.com/questions/27353026/qtableview-output-save-as-csv-or-txt
        with open('model_results.csv', 'w', newline='') as stream:
            writer = csv.writer(stream)
            for row in range(self.tableModel.rowCount()):
                rowdata = []
                for column in range(self.tableModel.columnCount()):
                    # print(self.tableModel.data(column))
                    item = self.tableModel._data.iloc[row][column]
                    if item is not None:
                        # rowdata.append(unicode(item.text()).encode('utf8'))
                        rowdata.append(str(item))
                    else:
                        rowdata.append('')
                writer.writerow(rowdata)


class SideMenu3(QVBoxLayout):
    """ Side menu for tab 3.
    
    Attributes:
        comparison: Comparison object that performs the calculations to
            determine which combination best fits the data.
        llfSpinBox: QSpinBox object, specifies the weighting used for the
            log-likelihood function in the comparison.
        aicSpinBox: QSpinBox object, specifies the weighting used for the
            Akaike information criterion in the comparison.
        bicSpinBox: QSpinBox object, specifies the weighting used for the
            Bayesian information criterion in the comparison.
        sseSpinBox: QSpinBox object, specifies the weighting used for the sum
            of squares error in the comparison.
        spinBoxChangedSignal: pyqtSignal, emits when any of the spin boxes for
            goodness-of-fit comparison weighting are changed.
        modelChangedSignal:
    """

    # signals
    spinBoxChangedSignal = pyqtSignal()
    modelChangedSignal = pyqtSignal(list)

    def __init__(self):
        """Initializes tab 3 side menu UI elements."""
        super().__init__()
        self._setupSideMenu()
        self.comparison = Comparison()

    def addSelectedModels(self, modelNames):
        """Adds model names to the model list widget.

        Args:
            modelNames: list of strings, name of each model to add to list
                widget.
        """
        self.modelListWidget.addItems(modelNames)

    def _setupSideMenu(self):
        """Creates side menu group boxes and adds them to the layout."""

        self.comparisonGroup = QGroupBox("Metric Weights (0-10)")
        self.comparisonGroup.setLayout(self._setupComparisonGroup())

        self.modelsGroup = QGroupBox("Select Model Results")
        # sets minumum size for side menu
        self.modelsGroup.setSizePolicy(QSizePolicy.MinimumExpanding, QSizePolicy.MinimumExpanding)
        self.modelsGroup.setLayout(self._setupModelsGroup())
        
        self.addWidget(self.comparisonGroup, 2)
        self.addWidget(self.modelsGroup, 7)

        self.addStretch(1)

    def _setupComparisonGroup(self):
        """Creates widget containing comparison weight spin boxes.

        Returns:
            A QGridLayout containing the created comparison spin boxes and
            corresponding labels.
        """
        comparisonLayout = QGridLayout()
        # self._createLabel("Metric", 0, 0, comparisonLayout)
        # self._createLabel("weights (0-10)", 0, 1, comparisonLayout)
        self._createLabel("LLF", 0, 0, comparisonLayout)
        self._createLabel("AIC", 1, 0, comparisonLayout)
        self._createLabel("BIC", 2, 0, comparisonLayout)
        self._createLabel("SSE", 3, 0, comparisonLayout)
        self.llfSpinBox = self._createSpinBox(0, 10, 0, 1, comparisonLayout)
        self.aicSpinBox = self._createSpinBox(0, 10, 1, 1, comparisonLayout)
        self.bicSpinBox = self._createSpinBox(0, 10, 2, 1, comparisonLayout)
        self.sseSpinBox = self._createSpinBox(0, 10, 3, 1, comparisonLayout)

        # vertical spacer at bottom of layout, keeps labels/spinboxes together at top
        # vspacer = QSpacerItem(20, 40, QSizePolicy.Maximum, QSizePolicy.Expanding)
        # comparisonLayout.addItem(vspacer, 5, 0, 1, -1)
        comparisonLayout.setColumnStretch(1, 1)

        return comparisonLayout

    def _setupModelsGroup(self):
        """Creates widget containing list of converged models.

        Returns:
            A QVBoxLayout containing the created model group.
        """
        modelGroupLayout = QVBoxLayout()
        self.modelListWidget = QListWidget()
        modelGroupLayout.addWidget(self.modelListWidget)
        self.modelListWidget.setSelectionMode(QAbstractItemView.MultiSelection)  # able to select multiple models
        self.modelListWidget.itemSelectionChanged.connect(self._emitModelChangedSignal)

        return modelGroupLayout

    def _createLabel(self, text, row, col, layout):
        """Creates a text label and adds it to the side menu layout.

        Args:
            text: The string of text the label displays.
            row: The row (int) of the QGroupBox widget to add the label to.
            col: The column (int) of the QGroupBox widget to add the label to.
            layout: The layout object that the label is added to.
        """
        label = QLabel(text)
        label.setSizePolicy(QSizePolicy(QSizePolicy.Preferred, QSizePolicy.Maximum))
        layout.addWidget(label, row, col)

    def _createSpinBox(self, minVal, maxVal, row, col, layout):
        """Creates a QSpinBox and adds it to the side menu layout.

        Current weighting values are allowed to be between 0 and 10.

        Args:
            minVal: The minimum value allowed by the spinbox (int).
            maxVal: The maximum value allowed by the spinbox (int).
            row: The row (int) of the QGroupBox widget to add the spinbox to.
            col: The column (int) of the QGroupBox widget to add the spinbox to.
            layout: The layout object that the spin box is added to.
        Returns:
            A created QSpinBox object with specified parameters.
        """
        spinBox = QSpinBox()
        spinBox.setRange(minVal, maxVal)
        spinBox.setValue(1)  # give equal weighting of 1 by default
        spinBox.valueChanged.connect(self._emitSpinBoxChangedSignal)
        layout.addWidget(spinBox, row, col)
        return spinBox

    def _emitModelChangedSignal(self):
        """
        """
        selectedModelNames = [item.text() for item in self.modelListWidget.selectedItems()]
        self.modelChangedSignal.emit(selectedModelNames)

    def _emitSpinBoxChangedSignal(self):
        """Emits signal if any goodness-of-fit spin box is changed."""
        self.spinBoxChangedSignal.emit()

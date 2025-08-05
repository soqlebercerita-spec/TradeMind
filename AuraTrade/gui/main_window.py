
"""
Main Window for AuraTrade Bot GUI
PyQt5-based interface with charts, dashboard, and controls
"""

from PyQt5.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
                           QTabWidget, QMenuBar, QStatusBar, QAction, 
                           QMessageBox, QSplitter, QPushButton, QLabel,
                           QTableWidget, QTableWidgetItem, QHeaderView,
                           QGroupBox, QGridLayout, QTextEdit, QProgressBar,
                           QSystemTrayIcon, QMenu)
from PyQt5.QtCore import Qt, QTimer, pyqtSignal, QThread, pyqtSlot
from PyQt5.QtGui import QIcon, QFont, QPixmap, QColor

from gui.dashboard import TradingDashboard
from gui.charts import TradingChartWidget
from utils.logger import Logger

class MainWindow(QMainWindow):
    """Professional trading interface"""
    
    def __init__(self, trading_engine, order_manager, risk_manager, data_manager):
        super().__init__()
        self.logger = Logger().get_logger()
        self.trading_engine = trading_engine
        self.order_manager = order_manager
        self.risk_manager = risk_manager
        self.data_manager = data_manager
        
        # Update timer
        self.update_timer = QTimer()
        self.update_timer.timeout.connect(self.update_display)
        self.update_timer.start(1000)  # Update every second
        
        # System tray
        self.tray_icon = None
        
        self.init_ui()
        self.logger.info("Main Window initialized")
    
    def init_ui(self):
        """Initialize the user interface"""
        try:
            self.setWindowTitle("AuraTrade Bot v2.0 - Professional Trading System")
            self.setGeometry(100, 100, 1400, 900)
            self.setMinimumSize(1200, 800)
            
            # Set application style
            self.setStyleSheet("""
                QMainWindow {
                    background-color: #1e1e1e;
                    color: #ffffff;
                }
                QTabWidget::pane {
                    border: 1px solid #444444;
                    background-color: #2d2d2d;
                }
                QTabBar::tab {
                    background-color: #3d3d3d;
                    color: #ffffff;
                    padding: 8px 16px;
                    margin-right: 2px;
                }
                QTabBar::tab:selected {
                    background-color: #0078d4;
                }
                QGroupBox {
                    font-weight: bold;
                    color: #ffffff;
                    border: 2px solid #444444;
                    border-radius: 5px;
                    margin-top: 10px;
                    padding-top: 10px;
                }
                QGroupBox::title {
                    subcontrol-origin: margin;
                    left: 10px;
                    padding: 0 5px 0 5px;
                }
                QPushButton {
                    background-color: #0078d4;
                    color: white;
                    border: none;
                    padding: 8px 16px;
                    border-radius: 4px;
                    font-weight: bold;
                }
                QPushButton:hover {
                    background-color: #106ebe;
                }
                QPushButton:pressed {
                    background-color: #005a9e;
                }
                QPushButton:disabled {
                    background-color: #666666;
                    color: #aaaaaa;
                }
                QLabel {
                    color: #ffffff;
                }
                QTableWidget {
                    background-color: #2d2d2d;
                    color: #ffffff;
                    gridline-color: #444444;
                    selection-background-color: #0078d4;
                }
                QHeaderView::section {
                    background-color: #3d3d3d;
                    color: #ffffff;
                    padding: 8px;
                    border: 1px solid #444444;
                    font-weight: bold;
                }
                QTextEdit {
                    background-color: #2d2d2d;
                    color: #ffffff;
                    border: 1px solid #444444;
                }
                QProgressBar {
                    border: 1px solid #444444;
                    border-radius: 5px;
                    text-align: center;
                }
                QProgressBar::chunk {
                    background-color: #0078d4;
                    border-radius: 4px;
                }
            """)
            
            # Create central widget and main layout
            central_widget = QWidget()
            self.setCentralWidget(central_widget)
            
            main_layout = QVBoxLayout(central_widget)
            main_layout.setContentsMargins(5, 5, 5, 5)
            
            # Create top toolbar
            self.create_toolbar(main_layout)
            
            # Create main content area
            self.create_main_content(main_layout)
            
            # Create status bar
            self.create_status_bar()
            
            # Create system tray
            self.create_system_tray()
            
            # Create menu bar
            self.create_menu_bar()
            
        except Exception as e:
            self.logger.error(f"Error initializing UI: {e}")
    
    def create_toolbar(self, parent_layout):
        """Create top toolbar with controls"""
        try:
            toolbar_group = QGroupBox("Control Panel")
            toolbar_layout = QHBoxLayout(toolbar_group)
            
            # Trading status
            self.status_label = QLabel("Status: Starting...")
            self.status_label.setStyleSheet("color: #ffa500; font-weight: bold;")
            toolbar_layout.addWidget(self.status_label)
            
            toolbar_layout.addStretch()
            
            # Control buttons
            self.start_btn = QPushButton("Start Trading")
            self.start_btn.clicked.connect(self.start_trading)
            self.start_btn.setStyleSheet("background-color: #28a745;")
            toolbar_layout.addWidget(self.start_btn)
            
            self.stop_btn = QPushButton("Stop Trading")
            self.stop_btn.clicked.connect(self.stop_trading)
            self.stop_btn.setStyleSheet("background-color: #dc3545;")
            self.stop_btn.setEnabled(False)
            toolbar_layout.addWidget(self.stop_btn)
            
            self.emergency_btn = QPushButton("EMERGENCY STOP")
            self.emergency_btn.clicked.connect(self.emergency_stop)
            self.emergency_btn.setStyleSheet("background-color: #ff0000; font-size: 12px;")
            toolbar_layout.addWidget(self.emergency_btn)
            
            parent_layout.addWidget(toolbar_group)
            
        except Exception as e:
            self.logger.error(f"Error creating toolbar: {e}")
    
    def create_main_content(self, parent_layout):
        """Create main content area with tabs"""
        try:
            # Create tab widget
            self.tab_widget = QTabWidget()
            
            # Overview tab
            self.overview_tab = self.create_overview_tab()
            self.tab_widget.addTab(self.overview_tab, "📊 Overview")
            
            # Positions tab
            self.positions_tab = self.create_positions_tab()
            self.tab_widget.addTab(self.positions_tab, "💼 Positions")
            
            # Charts tab
            self.charts_tab = self.create_charts_tab()
            self.tab_widget.addTab(self.charts_tab, "📈 Charts")
            
            # Logs tab
            self.logs_tab = self.create_logs_tab()
            self.tab_widget.addTab(self.logs_tab, "📝 Logs")
            
            parent_layout.addWidget(self.tab_widget)
            
        except Exception as e:
            self.logger.error(f"Error creating main content: {e}")
    
    def create_overview_tab(self):
        """Create overview dashboard tab"""
        try:
            tab = QWidget()
            layout = QHBoxLayout(tab)
            
            # Left panel - Account info
            left_panel = QWidget()
            left_layout = QVBoxLayout(left_panel)
            left_panel.setMaximumWidth(400)
            
            # Account Information
            account_group = QGroupBox("Account Information")
            account_layout = QGridLayout(account_group)
            
            self.balance_label = QLabel("$0.00")
            self.balance_label.setStyleSheet("font-size: 18px; font-weight: bold; color: #28a745;")
            account_layout.addWidget(QLabel("Balance:"), 0, 0)
            account_layout.addWidget(self.balance_label, 0, 1)
            
            self.equity_label = QLabel("$0.00")
            account_layout.addWidget(QLabel("Equity:"), 1, 0)
            account_layout.addWidget(self.equity_label, 1, 1)
            
            self.margin_label = QLabel("0.00%")
            account_layout.addWidget(QLabel("Margin Level:"), 2, 0)
            account_layout.addWidget(self.margin_label, 2, 1)
            
            self.pnl_label = QLabel("$0.00")
            account_layout.addWidget(QLabel("Daily P&L:"), 3, 0)
            account_layout.addWidget(self.pnl_label, 3, 1)
            
            left_layout.addWidget(account_group)
            
            # Trading Statistics
            stats_group = QGroupBox("Trading Statistics")
            stats_layout = QGridLayout(stats_group)
            
            self.trades_label = QLabel("0")
            stats_layout.addWidget(QLabel("Trades Today:"), 0, 0)
            stats_layout.addWidget(self.trades_label, 0, 1)
            
            self.winrate_label = QLabel("0.0%")
            stats_layout.addWidget(QLabel("Win Rate:"), 1, 0)
            stats_layout.addWidget(self.winrate_label, 1, 1)
            
            self.positions_label = QLabel("0")
            stats_layout.addWidget(QLabel("Open Positions:"), 2, 0)
            stats_layout.addWidget(self.positions_label, 2, 1)
            
            self.drawdown_label = QLabel("0.0%")
            stats_layout.addWidget(QLabel("Drawdown:"), 3, 0)
            stats_layout.addWidget(self.drawdown_label, 3, 1)
            
            left_layout.addWidget(stats_group)
            
            # Risk Status
            risk_group = QGroupBox("Risk Management")
            risk_layout = QVBoxLayout(risk_group)
            
            self.risk_status_label = QLabel("Risk Status: SAFE")
            self.risk_status_label.setStyleSheet("font-weight: bold; color: #28a745;")
            risk_layout.addWidget(self.risk_status_label)
            
            self.risk_progress = QProgressBar()
            self.risk_progress.setMaximum(100)
            self.risk_progress.setValue(25)
            risk_layout.addWidget(self.risk_progress)
            
            left_layout.addWidget(risk_group)
            left_layout.addStretch()
            
            layout.addWidget(left_panel)
            
            # Right panel - Dashboard chart
            try:
                self.dashboard = TradingDashboard()
                layout.addWidget(self.dashboard)
            except Exception as e:
                self.logger.warning(f"Could not create dashboard: {e}")
                placeholder = QLabel("Dashboard not available")
                placeholder.setAlignment(Qt.AlignCenter)
                layout.addWidget(placeholder)
            
            return tab
            
        except Exception as e:
            self.logger.error(f"Error creating overview tab: {e}")
            return QWidget()
    
    def create_positions_tab(self):
        """Create positions management tab"""
        try:
            tab = QWidget()
            layout = QVBoxLayout(tab)
            
            # Positions table
            self.positions_table = QTableWidget()
            self.positions_table.setColumnCount(9)
            self.positions_table.setHorizontalHeaderLabels([
                "Ticket", "Symbol", "Type", "Volume", "Entry", "Current", "SL", "TP", "Profit"
            ])
            
            # Auto-resize columns
            header = self.positions_table.horizontalHeader()
            header.setSectionResizeMode(QHeaderView.Stretch)
            
            layout.addWidget(self.positions_table)
            
            # Position controls
            controls_layout = QHBoxLayout()
            
            close_all_btn = QPushButton("Close All Positions")
            close_all_btn.clicked.connect(self.close_all_positions)
            close_all_btn.setStyleSheet("background-color: #dc3545;")
            controls_layout.addWidget(close_all_btn)
            
            controls_layout.addStretch()
            
            refresh_btn = QPushButton("Refresh")
            refresh_btn.clicked.connect(self.refresh_positions)
            controls_layout.addWidget(refresh_btn)
            
            layout.addLayout(controls_layout)
            
            return tab
            
        except Exception as e:
            self.logger.error(f"Error creating positions tab: {e}")
            return QWidget()
    
    def create_charts_tab(self):
        """Create charts tab"""
        try:
            tab = QWidget()
            layout = QVBoxLayout(tab)
            
            try:
                self.chart_widget = TradingChartWidget()
                layout.addWidget(self.chart_widget)
            except Exception as e:
                self.logger.warning(f"Could not create chart widget: {e}")
                placeholder = QLabel("Charts not available")
                placeholder.setAlignment(Qt.AlignCenter)
                layout.addWidget(placeholder)
            
            return tab
            
        except Exception as e:
            self.logger.error(f"Error creating charts tab: {e}")
            return QWidget()
    
    def create_logs_tab(self):
        """Create logs tab"""
        try:
            tab = QWidget()
            layout = QVBoxLayout(tab)
            
            self.log_text = QTextEdit()
            self.log_text.setReadOnly(True)
            self.log_text.setFont(QFont("Consolas", 9))
            layout.addWidget(self.log_text)
            
            # Log controls
            controls_layout = QHBoxLayout()
            
            clear_btn = QPushButton("Clear Logs")
            clear_btn.clicked.connect(self.log_text.clear)
            controls_layout.addWidget(clear_btn)
            
            controls_layout.addStretch()
            
            layout.addLayout(controls_layout)
            
            return tab
            
        except Exception as e:
            self.logger.error(f"Error creating logs tab: {e}")
            return QWidget()
    
    def create_status_bar(self):
        """Create status bar"""
        try:
            self.status_bar = QStatusBar()
            self.setStatusBar(self.status_bar)
            
            # Connection status
            self.connection_status = QLabel("Disconnected")
            self.connection_status.setStyleSheet("color: #dc3545; font-weight: bold;")
            self.status_bar.addPermanentWidget(self.connection_status)
            
            self.status_bar.showMessage("AuraTrade Bot Ready")
            
        except Exception as e:
            self.logger.error(f"Error creating status bar: {e}")
    
    def create_system_tray(self):
        """Create system tray icon"""
        try:
            if QSystemTrayIcon.isSystemTrayAvailable():
                self.tray_icon = QSystemTrayIcon(self)
                
                # Create tray menu
                tray_menu = QMenu()
                
                show_action = tray_menu.addAction("Show Window")
                show_action.triggered.connect(self.show)
                
                hide_action = tray_menu.addAction("Hide Window")
                hide_action.triggered.connect(self.hide)
                
                tray_menu.addSeparator()
                
                quit_action = tray_menu.addAction("Quit")
                quit_action.triggered.connect(self.close)
                
                self.tray_icon.setContextMenu(tray_menu)
                self.tray_icon.show()
                
        except Exception as e:
            self.logger.error(f"Error creating system tray: {e}")
    
    def create_menu_bar(self):
        """Create menu bar"""
        try:
            menubar = self.menuBar()
            
            # File menu
            file_menu = menubar.addMenu('File')
            
            export_action = QAction('Export Data', self)
            file_menu.addAction(export_action)
            
            file_menu.addSeparator()
            
            exit_action = QAction('Exit', self)
            exit_action.triggered.connect(self.close)
            file_menu.addAction(exit_action)
            
            # View menu
            view_menu = menubar.addMenu('View')
            
            minimize_action = QAction('Minimize to Tray', self)
            minimize_action.triggered.connect(self.hide)
            view_menu.addAction(minimize_action)
            
            # Help menu
            help_menu = menubar.addMenu('Help')
            
            about_action = QAction('About', self)
            about_action.triggered.connect(self.show_about)
            help_menu.addAction(about_action)
            
        except Exception as e:
            self.logger.error(f"Error creating menu bar: {e}")
    
    @pyqtSlot()
    def update_display(self):
        """Update all display elements"""
        try:
            if not self.trading_engine:
                return
            
            # Get current status
            status = self.trading_engine.get_status()
            
            # Update status label
            if status.get('running', False):
                self.status_label.setText("Status: ACTIVE")
                self.status_label.setStyleSheet("color: #28a745; font-weight: bold;")
                self.start_btn.setEnabled(False)
                self.stop_btn.setEnabled(True)
            else:
                self.status_label.setText("Status: STOPPED")
                self.status_label.setStyleSheet("color: #dc3545; font-weight: bold;")
                self.start_btn.setEnabled(True)
                self.stop_btn.setEnabled(False)
            
            # Update connection status
            if status.get('connected', False):
                self.connection_status.setText("Connected")
                self.connection_status.setStyleSheet("color: #28a745; font-weight: bold;")
            else:
                self.connection_status.setText("Disconnected")
                self.connection_status.setStyleSheet("color: #dc3545; font-weight: bold;")
            
            # Update account info
            self.balance_label.setText(f"${status.get('balance', 0.0):.2f}")
            self.equity_label.setText(f"${status.get('equity', 0.0):.2f}")
            self.pnl_label.setText(f"${status.get('daily_pnl', 0.0):.2f}")
            
            # Set P&L color
            pnl = status.get('daily_pnl', 0.0)
            if pnl > 0:
                self.pnl_label.setStyleSheet("color: #28a745; font-weight: bold;")
            elif pnl < 0:
                self.pnl_label.setStyleSheet("color: #dc3545; font-weight: bold;")
            else:
                self.pnl_label.setStyleSheet("color: #ffffff;")
            
            # Update statistics
            self.trades_label.setText(str(status.get('trades_today', 0)))
            self.winrate_label.setText(f"{status.get('win_rate', 0.0):.1f}%")
            self.positions_label.setText(str(status.get('open_positions', 0)))
            
            # Update positions table
            self.update_positions_table()
            
        except Exception as e:
            self.logger.error(f"Error updating display: {e}")
    
    def update_positions_table(self):
        """Update positions table"""
        try:
            if not hasattr(self, 'positions_table'):
                return
            
            positions = self.trading_engine.mt5_connector.get_positions()
            self.positions_table.setRowCount(len(positions))
            
            for row, position in enumerate(positions):
                self.positions_table.setItem(row, 0, QTableWidgetItem(str(position['ticket'])))
                self.positions_table.setItem(row, 1, QTableWidgetItem(position['symbol']))
                self.positions_table.setItem(row, 2, QTableWidgetItem('BUY' if position['type'] == 0 else 'SELL'))
                self.positions_table.setItem(row, 3, QTableWidgetItem(f"{position['volume']:.2f}"))
                self.positions_table.setItem(row, 4, QTableWidgetItem(f"{position['price_open']:.5f}"))
                self.positions_table.setItem(row, 5, QTableWidgetItem(f"{position['price_current']:.5f}"))
                self.positions_table.setItem(row, 6, QTableWidgetItem(f"{position['sl']:.5f}" if position['sl'] > 0 else "-"))
                self.positions_table.setItem(row, 7, QTableWidgetItem(f"{position['tp']:.5f}" if position['tp'] > 0 else "-"))
                
                # Profit with color
                profit_item = QTableWidgetItem(f"{position['profit']:.2f}")
                if position['profit'] > 0:
                    profit_item.setForeground(QColor('#28a745'))
                elif position['profit'] < 0:
                    profit_item.setForeground(QColor('#dc3545'))
                self.positions_table.setItem(row, 8, profit_item)
                
        except Exception as e:
            self.logger.error(f"Error updating positions table: {e}")
    
    def start_trading(self):
        """Start trading"""
        try:
            if self.trading_engine and not self.trading_engine.running:
                self.trading_engine.start()
                self.logger.info("Trading started from GUI")
        except Exception as e:
            self.logger.error(f"Error starting trading: {e}")
            QMessageBox.critical(self, "Error", f"Failed to start trading: {e}")
    
    def stop_trading(self):
        """Stop trading"""
        try:
            if self.trading_engine and self.trading_engine.running:
                self.trading_engine.stop()
                self.logger.info("Trading stopped from GUI")
        except Exception as e:
            self.logger.error(f"Error stopping trading: {e}")
            QMessageBox.critical(self, "Error", f"Failed to stop trading: {e}")
    
    def emergency_stop(self):
        """Emergency stop all trading"""
        try:
            reply = QMessageBox.question(self, 'Emergency Stop', 
                                       'Are you sure you want to EMERGENCY STOP?\nThis will close all positions and stop trading.',
                                       QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
            
            if reply == QMessageBox.Yes:
                if self.trading_engine:
                    self.trading_engine.stop()
                if self.order_manager:
                    self.order_manager.close_all_orders()
                if self.risk_manager:
                    self.risk_manager.emergency_stop = True
                
                self.logger.warning("EMERGENCY STOP activated from GUI")
                QMessageBox.information(self, "Emergency Stop", "Emergency stop activated. All trading stopped.")
                
        except Exception as e:
            self.logger.error(f"Error in emergency stop: {e}")
            QMessageBox.critical(self, "Error", f"Emergency stop error: {e}")
    
    def close_all_positions(self):
        """Close all positions"""
        try:
            reply = QMessageBox.question(self, 'Close All Positions', 
                                       'Are you sure you want to close all positions?',
                                       QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
            
            if reply == QMessageBox.Yes and self.order_manager:
                result = self.order_manager.close_all_orders()
                if result['success']:
                    QMessageBox.information(self, "Success", f"Closed {result['closed_count']} positions")
                else:
                    QMessageBox.warning(self, "Warning", f"Some positions could not be closed: {result['errors']}")
                    
        except Exception as e:
            self.logger.error(f"Error closing all positions: {e}")
            QMessageBox.critical(self, "Error", f"Failed to close positions: {e}")
    
    def refresh_positions(self):
        """Refresh positions table"""
        try:
            self.update_positions_table()
        except Exception as e:
            self.logger.error(f"Error refreshing positions: {e}")
    
    def show_about(self):
        """Show about dialog"""
        try:
            QMessageBox.about(self, "About AuraTrade Bot", 
                            "AuraTrade Bot v2.0\n\n"
                            "High-Performance Trading System\n"
                            "Target: 75%+ Win Rate\n"
                            "Conservative Risk Management\n\n"
                            "Professional Algorithmic Trading")
        except Exception as e:
            self.logger.error(f"Error showing about dialog: {e}")
    
    def closeEvent(self, event):
        """Handle window close event"""
        try:
            if self.tray_icon and self.tray_icon.isVisible():
                self.hide()
                event.ignore()
            else:
                event.accept()
        except Exception as e:
            self.logger.error(f"Error in close event: {e}")
            event.accept()

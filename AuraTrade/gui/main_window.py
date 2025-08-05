
"""
Main Window for AuraTrade Bot GUI
PyQt5-based interface with charts, dashboard, and controls
"""

from PyQt5.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
                           QTabWidget, QMenuBar, QStatusBar, QAction, 
                           QMessageBox, QSplitter)
from PyQt5.QtCore import Qt, QTimer, pyqtSignal
from PyQt5.QtGui import QIcon, QFont

from gui.dashboard import TradingDashboard
from gui.charts import TradingChartWidget
from utils.logger import Logger

class MainWindow(QMainWindow):
    """Main application window"""
    
    def __init__(self, trading_engine, order_manager, risk_manager, data_manager):
        super().__init__()
        
        self.trading_engine = trading_engine
        self.order_manager = order_manager
        self.risk_manager = risk_manager
        self.data_manager = data_manager
        self.logger = Logger().get_logger()
        
        self.setup_ui()
        self.setup_connections()
        
    def setup_ui(self):
        """Setup the main window UI"""
        self.setWindowTitle("AuraTrade - Institutional Trading Bot v1.0")
        self.setGeometry(100, 100, 1600, 1000)
        
        # Set application icon (if available)
        # self.setWindowIcon(QIcon('icon.png'))
        
        # Create central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Main layout
        main_layout = QVBoxLayout(central_widget)
        
        # Create splitter for resizable panes
        splitter = QSplitter(Qt.Horizontal)
        
        # Left pane - Dashboard
        self.dashboard = TradingDashboard(
            self.trading_engine,
            self.order_manager,
            self.risk_manager,
            self
        )
        splitter.addWidget(self.dashboard)
        
        # Right pane - Charts
        self.chart_widget = TradingChartWidget(self.data_manager, self)
        splitter.addWidget(self.chart_widget)
        
        # Set splitter proportions
        splitter.setSizes([1000, 600])
        
        main_layout.addWidget(splitter)
        
        # Setup menu bar
        self.create_menu_bar()
        
        # Setup status bar
        self.create_status_bar()
        
        # Apply styling
        self.apply_styling()
        
    def create_menu_bar(self):
        """Create the menu bar"""
        menubar = self.menuBar()
        
        # File menu
        file_menu = menubar.addMenu('File')
        
        # Export data action
        export_action = QAction('Export Data', self)
        export_action.triggered.connect(self.export_data)
        file_menu.addAction(export_action)
        
        file_menu.addSeparator()
        
        # Exit action
        exit_action = QAction('Exit', self)
        exit_action.setShortcut('Ctrl+Q')
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)
        
        # Trading menu
        trading_menu = menubar.addMenu('Trading')
        
        # Start trading action
        start_action = QAction('Start Trading', self)
        start_action.triggered.connect(self.start_trading)
        trading_menu.addAction(start_action)
        
        # Stop trading action
        stop_action = QAction('Stop Trading', self)
        stop_action.triggered.connect(self.stop_trading)
        trading_menu.addAction(stop_action)
        
        trading_menu.addSeparator()
        
        # Close all positions action
        close_all_action = QAction('Close All Positions', self)
        close_all_action.triggered.connect(self.close_all_positions)
        trading_menu.addAction(close_all_action)
        
        # Risk menu
        risk_menu = menubar.addMenu('Risk')
        
        # Emergency stop action
        emergency_action = QAction('Emergency Stop', self)
        emergency_action.triggered.connect(self.emergency_stop)
        risk_menu.addAction(emergency_action)
        
        # Reset daily limits action
        reset_limits_action = QAction('Reset Daily Limits', self)
        reset_limits_action.triggered.connect(self.reset_daily_limits)
        risk_menu.addAction(reset_limits_action)
        
        # Help menu
        help_menu = menubar.addMenu('Help')
        
        # About action
        about_action = QAction('About', self)
        about_action.triggered.connect(self.show_about)
        help_menu.addAction(about_action)
        
    def create_status_bar(self):
        """Create the status bar"""
        self.status_bar = self.statusBar()
        self.status_bar.showMessage("Ready")
        
        # Add connection status
        self.connection_status = self.status_bar.addPermanentWidget(
            self.create_status_label("MT5: Disconnected")
        )
        
    def create_status_label(self, text):
        """Create a status label widget"""
        from PyQt5.QtWidgets import QLabel
        
        label = QLabel(text)
        label.setStyleSheet("QLabel { color: red; font-weight: bold; }")
        return label
        
    def apply_styling(self):
        """Apply dark theme styling"""
        self.setStyleSheet("""
            QMainWindow {
                background-color: #2b2b2b;
                color: white;
            }
            
            QMenuBar {
                background-color: #3c3c3c;
                color: white;
                border: 1px solid #555;
            }
            
            QMenuBar::item {
                background-color: transparent;
                padding: 4px 8px;
            }
            
            QMenuBar::item:selected {
                background-color: #555;
            }
            
            QMenu {
                background-color: #3c3c3c;
                color: white;
                border: 1px solid #555;
            }
            
            QMenu::item:selected {
                background-color: #555;
            }
            
            QStatusBar {
                background-color: #3c3c3c;
                color: white;
                border-top: 1px solid #555;
            }
            
            QGroupBox {
                font-weight: bold;
                border: 2px solid #555;
                border-radius: 5px;
                margin-top: 1ex;
                color: white;
            }
            
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px 0 5px;
            }
            
            QLabel {
                color: white;
            }
            
            QPushButton {
                background-color: #4CAF50;
                border: none;
                color: white;
                padding: 8px 16px;
                text-align: center;
                font-size: 14px;
                border-radius: 4px;
            }
            
            QPushButton:hover {
                background-color: #45a049;
            }
            
            QPushButton:pressed {
                background-color: #3d8b40;
            }
            
            QTableWidget {
                background-color: #3c3c3c;
                color: white;
                gridline-color: #555;
                selection-background-color: #555;
            }
            
            QHeaderView::section {
                background-color: #555;
                color: white;
                border: 1px solid #777;
                padding: 4px;
            }
            
            QTextEdit {
                background-color: #1e1e1e;
                color: #00ff00;
                border: 1px solid #555;
                font-family: 'Courier New', monospace;
            }
        """)
        
    def setup_connections(self):
        """Setup signal connections"""
        # Connect dashboard emergency stop signal
        self.dashboard.emergency_stop_requested.connect(self.emergency_stop)
        
        # Setup timer for status updates
        self.status_timer = QTimer()
        self.status_timer.timeout.connect(self.update_status)
        self.status_timer.start(5000)  # Update every 5 seconds
        
    def update_status(self):
        """Update status bar information"""
        try:
            # Update connection status
            if hasattr(self.trading_engine, 'mt5_connector'):
                if self.trading_engine.mt5_connector.is_connected():
                    self.connection_status.setText("MT5: Connected ✅")
                    self.connection_status.setStyleSheet("QLabel { color: green; font-weight: bold; }")
                else:
                    self.connection_status.setText("MT5: Disconnected ❌")
                    self.connection_status.setStyleSheet("QLabel { color: red; font-weight: bold; }")
            
            # Update main status message
            if hasattr(self.trading_engine, 'running') and self.trading_engine.running:
                self.status_bar.showMessage("Trading Active - AuraTrade Running")
            else:
                self.status_bar.showMessage("Trading Stopped")
                
        except Exception as e:
            self.logger.error(f"Error updating status: {e}")
            self.status_bar.showMessage("Status Update Error")
    
    def start_trading(self):
        """Start trading engine"""
        try:
            if hasattr(self.trading_engine, 'start'):
                self.trading_engine.start()
                self.status_bar.showMessage("Trading Started")
                self.logger.info("Trading started via GUI")
            
        except Exception as e:
            self.logger.error(f"Error starting trading: {e}")
            QMessageBox.critical(self, "Error", f"Failed to start trading: {e}")
    
    def stop_trading(self):
        """Stop trading engine"""
        try:
            if hasattr(self.trading_engine, 'stop'):
                self.trading_engine.stop()
                self.status_bar.showMessage("Trading Stopped")
                self.logger.info("Trading stopped via GUI")
            
        except Exception as e:
            self.logger.error(f"Error stopping trading: {e}")
            QMessageBox.critical(self, "Error", f"Failed to stop trading: {e}")
    
    def close_all_positions(self):
        """Close all open positions"""
        try:
            reply = QMessageBox.question(
                self, 'Confirm', 
                'Are you sure you want to close all positions?',
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No
            )
            
            if reply == QMessageBox.Yes:
                closed_count = self.order_manager.close_all_positions()
                QMessageBox.information(self, "Success", f"Closed {closed_count} positions")
                self.logger.info(f"Closed {closed_count} positions via GUI")
            
        except Exception as e:
            self.logger.error(f"Error closing positions: {e}")
            QMessageBox.critical(self, "Error", f"Failed to close positions: {e}")
    
    def emergency_stop(self):
        """Trigger emergency stop"""
        try:
            reply = QMessageBox.warning(
                self, 'Emergency Stop', 
                'This will immediately close all positions and stop trading.\n\nAre you sure?',
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No
            )
            
            if reply == QMessageBox.Yes:
                # Stop trading engine
                if hasattr(self.trading_engine, 'stop'):
                    self.trading_engine.stop()
                
                # Emergency stop via order manager
                success = self.order_manager.emergency_stop()
                
                if success:
                    QMessageBox.information(self, "Emergency Stop", "Emergency stop executed successfully")
                    self.logger.warning("Emergency stop executed via GUI")
                else:
                    QMessageBox.critical(self, "Error", "Emergency stop failed")
            
        except Exception as e:
            self.logger.error(f"Error during emergency stop: {e}")
            QMessageBox.critical(self, "Error", f"Emergency stop failed: {e}")
    
    def reset_daily_limits(self):
        """Reset daily risk limits"""
        try:
            reply = QMessageBox.question(
                self, 'Reset Daily Limits', 
                'Reset daily risk limits and counters?',
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No
            )
            
            if reply == QMessageBox.Yes:
                self.risk_manager.reset_daily_limits()
                QMessageBox.information(self, "Success", "Daily limits reset successfully")
                self.logger.info("Daily limits reset via GUI")
            
        except Exception as e:
            self.logger.error(f"Error resetting daily limits: {e}")
            QMessageBox.critical(self, "Error", f"Failed to reset daily limits: {e}")
    
    def export_data(self):
        """Export trading data"""
        try:
            from PyQt5.QtWidgets import QFileDialog
            import json
            from datetime import datetime
            
            filename, _ = QFileDialog.getSaveFileName(
                self, 'Export Data', 
                f'auratrade_data_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json',
                'JSON Files (*.json)'
            )
            
            if filename:
                # Collect data to export
                export_data = {
                    'timestamp': datetime.now().isoformat(),
                    'order_history': self.order_manager.order_history,
                    'risk_summary': self.risk_manager.get_risk_summary(),
                    'order_statistics': self.order_manager.get_order_statistics()
                }
                
                # Save to file
                with open(filename, 'w') as f:
                    json.dump(export_data, f, indent=2, default=str)
                
                QMessageBox.information(self, "Success", f"Data exported to {filename}")
                self.logger.info(f"Data exported to {filename}")
            
        except Exception as e:
            self.logger.error(f"Error exporting data: {e}")
            QMessageBox.critical(self, "Error", f"Failed to export data: {e}")
    
    def show_about(self):
        """Show about dialog"""
        about_text = """
        <h2>AuraTrade - Institutional Trading Bot</h2>
        <p>Version 1.0.0</p>
        <p>Advanced automated trading system with:</p>
        <ul>
            <li>MetaTrader 5 integration</li>
            <li>Multiple trading strategies</li>
            <li>Advanced risk management</li>
            <li>Machine learning capabilities</li>
            <li>Real-time GUI dashboard</li>
        </ul>
        <p><b>Developed for professional trading</b></p>
        """
        
        QMessageBox.about(self, "About AuraTrade", about_text)
    
    def closeEvent(self, event):
        """Handle window close event"""
        try:
            reply = QMessageBox.question(
                self, 'Confirm Exit', 
                'Are you sure you want to exit AuraTrade?\n\nThis will stop all trading activity.',
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No
            )
            
            if reply == QMessageBox.Yes:
                # Stop trading engine
                if hasattr(self.trading_engine, 'stop'):
                    self.trading_engine.stop()
                
                self.logger.info("Application closed via GUI")
                event.accept()
            else:
                event.ignore()
                
        except Exception as e:
            self.logger.error(f"Error during application close: {e}")
            event.accept()  # Force close if error occurs

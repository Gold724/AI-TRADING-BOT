# test_deploy.py

import os
import sys
import unittest
from unittest.mock import patch, MagicMock

# Import the deployment system
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Mock the imports that might not exist yet
sys.modules['integration_test'] = MagicMock()
sys.modules['monitoring_system'] = MagicMock()
sys.modules['capital_allocator'] = MagicMock()
sys.modules['model_refinement'] = MagicMock()
sys.modules['metrics_dashboard'] = MagicMock()
sys.modules['live_trading'] = MagicMock()
sys.modules['emergency_protocol'] = MagicMock()
sys.modules['signal_router'] = MagicMock()
sys.modules['memory_engine'] = MagicMock()
sys.modules['strategy_manager'] = MagicMock()
sys.modules['risk_control'] = MagicMock()

# Now import the deployer
from deploy import TradingSystemDeployer

class TestDeployment(unittest.TestCase):
    """Test cases for the TradingSystemDeployer class"""
    
    def setUp(self):
        """Set up test environment"""
        # Create a test config file path in the current directory
        self.test_config_path = os.path.join(os.getcwd(), "test_deploy_config.json")
        
        # Remove test config file if it exists
        if os.path.exists(self.test_config_path):
            os.remove(self.test_config_path)
    
    def tearDown(self):
        """Clean up test environment"""
        # Remove test config file if it exists
        if os.path.exists(self.test_config_path):
            os.remove(self.test_config_path)
    
    def test_load_config(self):
        """Test loading configuration"""
        # Create deployer with test config path
        deployer = TradingSystemDeployer(config_path=self.test_config_path)
        
        # Check if config has expected keys
        self.assertIn("environment", deployer.config)
        self.assertIn("run_integration_test", deployer.config)
        self.assertIn("components", deployer.config)
        self.assertIn("broker", deployer.config)
    
    @patch("deploy.IntegrationTest")
    def test_run_integration_test(self, mock_integration_test):
        """Test running integration test"""
        # Mock integration test result
        mock_instance = MagicMock()
        mock_instance.run_all_tests.return_value = {"success": True, "message": "All tests passed"}
        mock_integration_test.return_value = mock_instance
        
        # Create deployer with test config path
        deployer = TradingSystemDeployer(config_path=self.test_config_path)
        
        # Run integration test
        result = deployer.run_integration_test()
        
        # Check if integration test was called
        mock_integration_test.assert_called_once()
        mock_instance.run_all_tests.assert_called_once()
        
        # Check if result is True
        self.assertTrue(result)
    
    @patch("deploy.EmergencyProtocol")
    @patch("deploy.LiveTrading")
    @patch("deploy.MonitoringSystem")
    @patch("deploy.CapitalAllocator")
    @patch("deploy.ModelRefinement")
    @patch("deploy.SignalRouter")
    def test_initialize_components(self, mock_signal_router, mock_model_refinement, 
                                  mock_capital_allocator, mock_monitoring_system, 
                                  mock_live_trading, mock_emergency_protocol):
        """Test initializing components"""
        # Create deployer with test config path
        deployer = TradingSystemDeployer(config_path=self.test_config_path)
        
        # Initialize components
        result = deployer.initialize_components()
        
        # Check if components were initialized
        mock_emergency_protocol.assert_called_once()
        mock_live_trading.assert_called_once()
        mock_monitoring_system.assert_called_once()
        mock_capital_allocator.assert_called_once()
        mock_model_refinement.assert_called_once()
        mock_signal_router.assert_called_once()
        
        # Check if result is True
        self.assertTrue(result)
        
        # Check if components were stored
        self.assertIn("emergency_protocol", deployer.components)
        self.assertIn("live_trading", deployer.components)
        self.assertIn("monitoring_system", deployer.components)
        self.assertIn("capital_allocator", deployer.components)
        self.assertIn("model_refinement", deployer.components)
        self.assertIn("signal_router", deployer.components)
    
    @patch("deploy.TradingSystemDeployer.run_integration_test")
    @patch("deploy.TradingSystemDeployer.initialize_components")
    @patch("deploy.TradingSystemDeployer.start_components")
    def test_deploy(self, mock_start_components, mock_initialize_components, mock_run_integration_test):
        """Test deploying the system"""
        # Mock method results
        mock_run_integration_test.return_value = True
        mock_initialize_components.return_value = True
        mock_start_components.return_value = True
        
        # Create deployer with test config path
        deployer = TradingSystemDeployer(config_path=self.test_config_path)
        
        # Deploy the system
        result = deployer.deploy()
        
        # Check if methods were called
        mock_run_integration_test.assert_called_once()
        mock_initialize_components.assert_called_once()
        mock_start_components.assert_called_once()
        
        # Check if result is True
        self.assertTrue(result)

if __name__ == "__main__":
    unittest.main()